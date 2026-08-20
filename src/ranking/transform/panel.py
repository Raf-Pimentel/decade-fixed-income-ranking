"""One row of numbers per fund.

Takes a year of daily quotas and collapses it into the ten figures the ranking
scores on. The arithmetic itself lives in `metrics`; this module's job is to
apply it to real data, which means dealing with funds that started mid-period,
series that stop early, and the point-in-time rule.

A fund is dropped here rather than scored badly when its numbers cannot be
computed honestly — a quota that never moved has no volatility, and a
return-per-risk of infinity would put it straight at the top.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from ranking.transform import metrics

MINIMUM_OBSERVATIONS = 2


def benchmark_window(frame: pl.DataFrame, start: dt.date, end: dt.date) -> pl.DataFrame:
    """The benchmark restricted to the period being measured.

    Compounding the benchmark over a different window than the fund is an easy
    mistake and an invisible one: the excess return is simply wrong, by an
    amount nobody can see without recomputing it.
    """
    return frame.filter((pl.col("data") >= start) & (pl.col("data") <= end)).sort("data")


def build(
    series: pl.DataFrame,
    benchmark_rate: float,
    reference_date: dt.date,
) -> pl.DataFrame:
    """Collapse a daily panel into one row per fund.

    `benchmark_rate` is the benchmark's compounded return over the same window,
    already computed — passing the number rather than the series keeps this
    function honest about using exactly one window for both sides.
    """
    windowed = series.filter(pl.col("data") <= reference_date).sort("cnpj_classe", "data")

    rows: list[dict[str, object]] = []
    for (cnpj,), group in windowed.group_by(["cnpj_classe"], maintain_order=True):
        quotas = group["valor_cota"].to_numpy()
        if quotas.size < MINIMUM_OBSERVATIONS or not np.all(np.isfinite(quotas)):
            continue
        if np.any(quotas <= 0):
            continue

        daily = metrics.daily_returns(quotas)
        total_return = metrics.cumulative_return(quotas)
        volatility = metrics.annualised_volatility(daily)
        average_assets = float(np.nanmean(group["patrimonio_liquido"].to_numpy()))

        # A quota that has not moved all period is not a riskless fund, it is
        # an unpriced one. Leaving the ratio null keeps it out of the ranking
        # instead of putting it on top.
        per_risk = (
            metrics.return_per_risk(total_return, benchmark_rate, volatility)
            if volatility > 0
            else None
        )

        rows.append(
            {
                "cnpj_classe": cnpj,
                "observacoes": int(quotas.size),
                "primeira_data": group["data"].min(),
                "ultima_data": group["data"].max(),
                "retorno": total_return,
                "excesso": metrics.excess_return(total_return, benchmark_rate),
                "volatilidade": volatility,
                "retorno_por_risco": per_risk,
                "pior_queda": metrics.max_drawdown(quotas),
                "dias_negativos": metrics.negative_day_share(daily),
                "volatilidade_baixa": metrics.downside_volatility(daily),
                "patrimonio_medio": average_assets,
                "estabilidade_fluxo": (
                    metrics.flow_stability(
                        group["captacao"].to_numpy(),
                        group["resgate"].to_numpy(),
                        average_assets,
                    )
                    if average_assets > 0
                    else None
                ),
            }
        )

    if not rows:
        return pl.DataFrame(schema=_EMPTY_SCHEMA)
    return pl.DataFrame(rows)


_EMPTY_SCHEMA: dict[str, pl.DataType] = {
    "cnpj_classe": pl.String(),
    "observacoes": pl.Int64(),
    "primeira_data": pl.Date(),
    "ultima_data": pl.Date(),
    "retorno": pl.Float64(),
    "excesso": pl.Float64(),
    "volatilidade": pl.Float64(),
    "retorno_por_risco": pl.Float64(),
    "pior_queda": pl.Float64(),
    "dias_negativos": pl.Float64(),
    "volatilidade_baixa": pl.Float64(),
    "patrimonio_medio": pl.Float64(),
    "estabilidade_fluxo": pl.Float64(),
}
