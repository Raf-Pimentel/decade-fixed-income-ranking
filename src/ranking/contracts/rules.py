"""Business rules the schema cannot express.

A schema can say "the quota must be positive". It cannot say "the quota jumped
fifty percent overnight, which is either a data error or an amortisation, and
we do not know which". Those judgements live here, one named function each, so
that every rule can be pointed at and argued with.
"""

from __future__ import annotations

import polars as pl


def flag_implausible_moves(frame: pl.DataFrame, threshold: float = 0.20) -> pl.DataFrame:
    """Mark unusually large daily moves — and mark only.

    Dropping these rows would be the obvious thing and the wrong one. A fund
    that amortises its quota shows a large fall with no loss to the investor,
    and deleting that day would turn a real corporate action into a hole in
    the series, quietly changing every return computed across it.

    Marking keeps the series whole and leaves the judgement to a human.
    """
    return frame.sort("cnpj_classe", "data").with_columns(
        (
            (pl.col("valor_cota") / pl.col("valor_cota").shift(1).over("cnpj_classe") - 1)
            .abs()
            .gt(threshold)
            .fill_null(False)
        ).alias("implausible_move")
    )


def flag_stale_quotas(frame: pl.DataFrame, max_days: int = 10) -> pl.DataFrame:
    """Mark funds whose quota has not moved for too long.

    A quota repeating to the last decimal for weeks is not a calm fund, it is
    a fund that stopped being priced. Its volatility would read as near zero
    and its return per unit of risk would be spectacular, which is exactly the
    kind of artefact that wins a naive ranking.
    """
    unchanged = (
        pl.col("valor_cota").eq(pl.col("valor_cota").shift(1).over("cnpj_classe")).fill_null(False)
    )
    return (
        frame.sort("cnpj_classe", "data")
        .with_columns(unchanged.alias("_unchanged"))
        .with_columns(
            # A new run starts on every day the quota actually moved, so all
            # consecutive frozen days share the run id of the last real move.
            # Counting total frozen days instead would flag an ordinary fund
            # that happened to be flat on twelve scattered days of the year.
            (~pl.col("_unchanged")).cum_sum().over("cnpj_classe").alias("_run_id")
        )
        .with_columns(pl.len().over("cnpj_classe", "_run_id").alias("_run_length"))
        .with_columns(
            # the run holds one day that moved plus the frozen ones after it
            (pl.col("_unchanged") & ((pl.col("_run_length") - 1) >= max_days)).alias("stale_quota")
        )
        .drop("_unchanged", "_run_id", "_run_length")
    )
