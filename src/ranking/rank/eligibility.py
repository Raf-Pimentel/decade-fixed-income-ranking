"""Which funds a given client can actually buy.

Applied **before** anything is scored. Ranking everyone together and filtering
afterwards would score a retail fund against a universe it has no access to,
and the percentile it earned would mean nothing.

Nothing here is invented: the target-investor field is the CVM's own, and the
redemption and minimum-investment limits come from what the fund itself filed.
"""

from __future__ import annotations

import polars as pl

from ranking.config import Eligibility


def apply(
    funds: pl.DataFrame,
    target_investor: list[str] | None,
    max_minimum_investment_brl: float | None,
    max_redemption_days: int | None,
) -> pl.DataFrame:
    """Keep only the funds this profile can reach.

    A `None` limit means no limit, which is different from a limit of zero —
    the distinction matters because the qualified profile genuinely has no
    minimum-investment ceiling.
    """
    result = funds
    if target_investor is not None and "publico_alvo" in result.columns:
        result = result.filter(pl.col("publico_alvo").is_in(target_investor))
    if max_minimum_investment_brl is not None and "aplicacao_minima" in result.columns:
        result = result.filter(
            pl.col("aplicacao_minima").is_null()
            | (pl.col("aplicacao_minima") <= max_minimum_investment_brl)
        )
    if max_redemption_days is not None and "dias_resgate" in result.columns:
        result = result.filter(pl.col("dias_resgate") <= max_redemption_days)
    return result


def for_profile(funds: pl.DataFrame, eligibility: Eligibility) -> pl.DataFrame:
    """The same thing, driven straight from the profile's configuration."""
    return apply(
        funds,
        target_investor=eligibility.target_investor,
        max_minimum_investment_brl=eligibility.max_minimum_investment_brl,
        max_redemption_days=eligibility.max_redemption_days,
    )
