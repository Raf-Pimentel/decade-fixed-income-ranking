"""Which funds compete, and how many survive each cut.

The counts are not diagnostics. They are the product. A pipeline that quietly
loses half the universe still emits valid rows, still passes every schema, and
still produces a confident ranking of the wrong funds. Recording the size of
the universe at every step, and comparing it against numbers measured in
advance, is what makes that visible.

Every filter here is read from configuration. Decade has not yet confirmed the
exact definition of "fixed income", and when they do, nothing in this file
changes.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import polars as pl

from ranking.config import Filters


@dataclass(frozen=True)
class UniverseResult:
    """The eligible funds, plus the audit trail of how many were lost where."""

    funds: pl.DataFrame
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def by_target_investor(self) -> dict[str, int]:
        if self.funds.is_empty():
            return {}
        grouped = self.funds.group_by("publico_alvo").len()
        return dict(zip(grouped["publico_alvo"], grouped["len"], strict=True))


def summarise_series(series: pl.DataFrame, reference_date: dt.date) -> pl.DataFrame:
    """Collapse a daily series into one row per fund.

    Sorting before taking the last value is deliberate. Grouping without an
    explicit order gives whichever row the engine happened to hold, so "the
    latest net assets" would be arbitrary and would change between runs, which
    would break reproducibility in a way that is very hard to spot.
    """
    return (
        series.filter(pl.col("data") <= reference_date)
        .sort("cnpj_classe", "data")
        .group_by("cnpj_classe", maintain_order=True)
        .agg(
            pl.len().alias("observacoes"),
            pl.col("data").last().alias("ultima_data"),
            pl.col("data").first().alias("primeira_data"),
            pl.col("patrimonio_liquido").last().alias("patrimonio_liquido"),
            pl.col("cotistas").last().alias("cotistas"),
        )
    )


def blank_undisclosed_fees(funds: pl.DataFrame) -> pl.DataFrame:
    """Stop scoring on an admin fee of exactly zero.

    A fifth of the funds with fewer than a hundred shareholders declare a fee
    of exactly zero, against six per cent everywhere else. These are master and
    institutional vehicles whose fee is charged at the feeder or by the
    distributor. The money is taken, just not at this level.

    Cost carries the heaviest weight in both profiles, so a zero taken at face
    value hands the best possible percentile to whoever disclosed the least.
    Blanking it scores those funds neutrally instead: we do not know what they
    cost, and saying so is more honest than pretending they are free.

    The filed value is kept alongside, because the delivery should report what
    the fund actually declared.
    """
    if "taxa_adm" not in funds.columns:
        return funds
    # `taxa_adm_declarada` may already carry the filed value, put there by the
    # fee measurement before this runs. Overwriting it with the measured figure
    # would lose the very comparison the delivery exists to show.
    declared = (
        pl.col("taxa_adm_declarada")
        if "taxa_adm_declarada" in funds.columns
        else pl.col("taxa_adm")
    )
    return funds.with_columns(
        declared.alias("taxa_adm_declarada"),
        (pl.col("taxa_adm") == 0).fill_null(False).alias("taxa_zero_declarada"),
    ).with_columns(
        pl.when(pl.col("taxa_adm") == 0).then(None).otherwise(pl.col("taxa_adm")).alias("taxa_adm")
    )


def reachable_by_individuals(funds: pl.DataFrame, profile: pl.DataFrame) -> pl.DataFrame:
    """Keep the classes that a person is actually inside.

    The delivery is a list for a retail individual, and the CVM's
    target-investor field cannot support that claim. It records whether a class
    is open to non-qualified investors, not whether it admits a person rather
    than a company, so a class sold only to companies, pension schemes and
    insurers passes every formal filter and is still not a product a person
    buys. Four such classes reached the published top five before this rule
    existed, and one of them permits individuals in its own regulation while
    holding none. See decision D-050.

    What settles it is a count rather than a clause. The CVM publishes the
    shareholder base of every class broken down by kind, so the question stops
    being "who is allowed in" and becomes "who is in".

    Two choices keep the rule from removing more than it should. Money held
    through a distributor is reported as one opaque line rather than as the
    people behind it, and those people are the retail investor this delivery is
    written for, so that line counts in favour of the class. And a class with
    no filing at all is kept: absence of the report is not evidence of absence
    of people.

    There is no threshold. A single individual is enough, which is what makes
    the rule impossible to tune towards a result.
    """
    if profile.is_empty() or "cnpj_classe" not in profile.columns:
        return funds

    reachable = (
        profile.filter((pl.col("cotistas_pf") > 0) | (pl.col("cotistas_distribuidor") > 0))
        .select("cnpj_classe")
        .unique()
    )
    filed = profile.select("cnpj_classe").unique()
    return funds.join(
        pl.concat(
            [reachable, funds.select("cnpj_classe").join(filed, on="cnpj_classe", how="anti")]
        ).unique(),
        on="cnpj_classe",
        how="semi",
    )


def build(
    registry: pl.DataFrame,
    series: pl.DataFrame,
    terms: pl.DataFrame,
    filters: Filters,
    reference_date: dt.date,
    investor_profile: pl.DataFrame | None = None,
) -> UniverseResult:
    """Apply every eligibility rule in order, counting as we go."""
    counts: dict[str, int] = {}
    frame = registry
    counts["registered_classes"] = len(frame)

    frame = frame.filter(
        pl.any_horizontal(
            [pl.col("classificacao").str.contains(name) for name in filters.classification]
        )
    )
    counts["fixed_income"] = len(frame)

    frame = frame.filter(pl.col("situacao").is_in(filters.status))
    counts["operating"] = len(frame)

    frame = frame.filter(pl.col("forma_condominio").is_in(filters.condominium))
    counts["open_ended"] = len(frame)

    if filters.exclude_exclusive:
        frame = frame.filter(pl.col("exclusivo") != "S")
    counts["non_exclusive"] = len(frame)

    summary = summarise_series(series, reference_date)
    frame = frame.join(summary, on="cnpj_classe", how="inner")
    counts["with_quota_series"] = len(frame)

    frame = frame.filter(pl.col("observacoes") >= filters.min_observations)
    counts["with_enough_observations"] = len(frame)

    frame = frame.filter(pl.col("patrimonio_liquido") >= filters.min_net_assets_brl)
    counts["above_min_assets"] = len(frame)

    frame = frame.filter(pl.col("cotistas") >= filters.min_shareholders)
    counts["above_min_shareholders"] = len(frame)

    # One row per fund, whatever the statement file contains. The CVM registry
    # already proved that a source can repeat a key, and a fund appearing twice
    # here would be ranked twice.
    unique_terms = terms.unique(subset=["cnpj_classe"], keep="last", maintain_order=True)
    if filters.require_fee_and_redemption:
        before = len(frame)
        frame = frame.join(unique_terms, on="cnpj_classe", how="inner").filter(
            pl.col("taxa_adm").is_not_null() & pl.col("dias_resgate").is_not_null()
        )
        if len(frame) > before:  # pragma: no cover - guarded by a test
            raise ValueError("joining the statement multiplied funds; check for repeated keys")
    else:
        frame = frame.join(unique_terms, on="cnpj_classe", how="left")
    counts["with_fee_and_redemption"] = len(frame)

    # Last, because it is the only step that asks about the holder rather than
    # about the fund, and because a class removed here passed everything else.
    if investor_profile is not None:
        frame = reachable_by_individuals(frame, investor_profile)
    counts["reachable_by_individuals"] = len(frame)

    return UniverseResult(funds=blank_undisclosed_fees(frame), counts=counts)
