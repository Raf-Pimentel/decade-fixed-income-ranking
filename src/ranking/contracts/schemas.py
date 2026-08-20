"""What each stage is allowed to hand to the next one.

Two different jobs live here, and they are deliberately separate:

- **Triage.** Every incoming row either passes or goes to quarantine *with a
  written reason*. Nothing is dropped silently, because a filter you cannot
  inspect is indistinguishable from a bug.
- **Guarantee.** What leaves the stage is then checked against a declared
  schema. If the clean set ever fails that check, the triage rules are wrong —
  it is a second lock on the same door, pointing at a different suspect.

The output contract at the bottom is the one another team depends on, so it
carries a version number.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

import pandera.polars as pa
import polars as pl
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ranking.transform import normalize

# ---------------------------------------------------------------------------
# The declared shape of a validated daily report
# ---------------------------------------------------------------------------


class DailyReport(pa.DataFrameModel):
    """What a clean daily-report table looks like, by declaration.

    This is not where rows are rejected — it is the assertion that the rows
    which survived rejection really are sound.
    """

    cnpj_classe: str = pa.Field(str_matches=r"^\d{14}$")
    data: pl.Date = pa.Field(nullable=False)
    valor_cota: float = pa.Field(gt=0, nullable=False)
    patrimonio_liquido: float = pa.Field(ge=0, nullable=True)
    cotistas: int = pa.Field(ge=0, nullable=True)

    class Config:
        strict = False  # extra columns are fine; missing declared ones are not


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------

NATURAL_KEY = ["cnpj_classe", "data"]


@dataclass(frozen=True)
class ValidationResult:
    """The full account of what happened to every row that came in.

    `len(clean) + len(quarantined) + dropped_future + deduplicated` must equal
    the number of rows received. A row that cannot be accounted for is a bug.
    """

    clean: pl.DataFrame
    quarantined: pl.DataFrame
    dropped_future: int
    deduplicated: int

    @property
    def received(self) -> int:
        return len(self.clean) + len(self.quarantined) + self.dropped_future + self.deduplicated

    @property
    def quarantined_share(self) -> float:
        return len(self.quarantined) / self.received if self.received else 0.0


def _cnpj_validity(frame: pl.DataFrame) -> pl.Expr:
    """Check digits, evaluated once per distinct CNPJ rather than per row.

    A monthly file has half a million rows and twenty-five thousand distinct
    funds, so checking the value rather than the row is twenty times less work.
    """
    distinct = frame.get_column("cnpj_classe").unique().drop_nulls().to_list()
    valid = [value for value in distinct if normalize.is_valid_cnpj(value)]
    return pl.col("cnpj_classe").is_in(valid)


def _rejection_reason(frame: pl.DataFrame) -> pl.Expr:
    """The first thing wrong with a row, or null if nothing is.

    Order matters only for which reason gets reported; a row with two problems
    is quarantined either way. The CNPJ comes first because a row we cannot
    identify cannot be usefully described any further.
    """
    return (
        pl.when(pl.col("cnpj_classe").is_null() | (pl.col("cnpj_classe").str.len_chars() != 14))
        .then(pl.lit("cnpj: not 14 digits"))
        .when(~_cnpj_validity(frame))
        .then(pl.lit("cnpj: check digits do not match"))
        .when(pl.col("data").is_null())
        .then(pl.lit("date: could not be parsed"))
        .when(pl.col("valor_cota").is_null())
        .then(pl.lit("quota: missing"))
        .when(pl.col("valor_cota") <= 0)
        .then(pl.lit("quota: not positive"))
        .when(pl.col("patrimonio_liquido") < 0)
        .then(pl.lit("net assets: negative"))
        .otherwise(None)
        .alias("reason")
    )


def validate_daily_report(frame: pl.DataFrame, reference_date: dt.date) -> ValidationResult:
    """Split a daily report into what can be used and what cannot."""
    received = len(frame)

    # 1. Collapse repeats of the natural key. The CVM restates by republishing,
    #    and the later row is the corrected one.
    deduped = frame.unique(subset=NATURAL_KEY, keep="last", maintain_order=True)
    deduplicated = received - len(deduped)

    # 2. Drop anything dated after the reference date. This is the point-in-time
    #    rule, and it is enforced here rather than trusted to callers: a single
    #    leaked future row would quietly invalidate the backtest.
    future = deduped.filter(pl.col("data").is_not_null() & (pl.col("data") > reference_date))
    present = deduped.filter(pl.col("data").is_null() | (pl.col("data") <= reference_date))

    # 3. Triage the rest, keeping the reason attached.
    judged = present.with_columns(_rejection_reason(present))
    quarantined = judged.filter(pl.col("reason").is_not_null())
    clean = judged.filter(pl.col("reason").is_null()).drop("reason")

    return ValidationResult(
        clean=clean,
        quarantined=quarantined,
        dropped_future=len(future),
        deduplicated=deduplicated,
    )


def assert_matches_contract(frame: pl.DataFrame) -> None:
    """Belt and braces: the clean set must satisfy the declared schema.

    If this raises, the triage rules let something through — the fault is in
    `_rejection_reason`, not in the data.
    """
    DailyReport.validate(frame, lazy=True)


# ---------------------------------------------------------------------------
# The output contract — what another team consumes
# ---------------------------------------------------------------------------


class RankedFund(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    cnpj_classe: str
    name: str
    manager: str | None = None
    peer_group: str | None = None
    score: float
    appearance_rate: float = Field(
        description="share of simulations in which this fund stayed in the top 5"
    )
    metrics: dict[str, float | int | str | None] = Field(default_factory=dict)
    percentiles: dict[str, float] = Field(default_factory=dict)
    rationale: str = ""


class ProfileRanking(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str
    label: str
    eligible_universe_size: int
    weights: dict[str, int]
    top: list[RankedFund]
    top_n: int = 5

    @model_validator(mode="after")
    def _top_fits(self) -> ProfileRanking:
        if len(self.top) > self.top_n:
            raise ValueError(f"top list has {len(self.top)} funds but top_n is {self.top_n}")
        return self


class RankingOutput(BaseModel):
    """Versioned so that another team can depend on it.

    A breaking change to this shape is a major version bump, and that is the
    whole point of writing the number into the file.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    reference_date: dt.date
    lookback_months: int
    sources: dict[str, Any]
    profiles: list[ProfileRanking]
    generated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.UTC))
    benchmark_by_group: dict[str, str] = Field(default_factory=dict)
    benchmark_label: str = "CDI"
