"""Which funds compete, and how many survive each cut.

The counts are not diagnostics — they are the product. A pipeline that quietly
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
    latest net assets" would be arbitrary and would change between runs — which
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


def build(
    registry: pl.DataFrame,
    series: pl.DataFrame,
    terms: pl.DataFrame,
    filters: Filters,
    reference_date: dt.date,
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

    return UniverseResult(funds=frame, counts=counts)
