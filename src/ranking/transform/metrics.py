"""The financial arithmetic.

This is the smallest module in the project and the one most worth getting
right. A wrong formula here does not crash, does not look wrong, and does not
show up in any log — it just produces a confident ranking of the wrong funds.
Everything is a plain function over plain numbers so that each one can be
checked against an invariant that must hold whatever the data is.

Two conventions, both load-bearing:

- **Returns are simple, not logarithmic.** Simple returns chain by
  multiplication straight back to the endpoint ratio, so the day-by-day path
  and the ends always agree. Mixing the two conventions is the classic way to
  produce numbers that are almost right.
- **The year has 252 days, not 365.** Funds are priced on business days.
  Annualising with 365 would inflate every volatility by about 20% and
  reshuffle anything ranked on risk.

Nothing here reads a file or knows what a fund is.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

BUSINESS_DAYS_PER_YEAR = 252

Series = Sequence[float] | npt.NDArray[np.float64]


def _as_quotas(values: Series) -> npt.NDArray[np.float64]:
    """Validate a quota series once, loudly, before anything is computed."""
    array = np.asarray(values, dtype=np.float64)
    if array.size < 2:
        raise ValueError(f"a return needs at least two observations, got {array.size}")
    if not np.all(np.isfinite(array)):
        raise ValueError("quota series contains missing or infinite values")
    if np.any(array <= 0):
        raise ValueError("quota values must be positive; a quota of zero has no meaning")
    return array


def cumulative_return(quotas: Series) -> float:
    """Total return over the period, from the first quota to the last.

    Only the ends matter. What happened in between belongs to the risk
    measures, not to this one.
    """
    array = _as_quotas(quotas)
    return float(array[-1] / array[0] - 1)


def daily_returns(quotas: Series) -> npt.NDArray[np.float64]:
    """Day-on-day simple returns.

    Chaining these by multiplication reproduces `cumulative_return` exactly,
    which is the invariant that keeps the two consistent.
    """
    array = _as_quotas(quotas)
    return np.asarray(array[1:] / array[:-1] - 1, dtype=np.float64)


def compound(rates: Series) -> float:
    """Chain a series of period rates into one.

    Adding them instead is the standard way to misstate a benchmark: 1% a day
    for a hundred days is 170%, not 100%. Over a year of CDI at Brazilian
    levels the gap is worth several percentage points, which is larger than
    the differences this project is trying to rank on.
    """
    array = np.asarray(rates, dtype=np.float64)
    if array.size == 0:
        return 0.0
    if not np.all(np.isfinite(array)):
        raise ValueError("rate series contains missing or infinite values")
    return float(np.prod(1.0 + array) - 1.0)


def excess_return(fund_return: float, benchmark_return: float) -> float:
    """What the fund added over the benchmark it is measured against.

    Every group is measured against the CDI, including the inflation-linked
    funds, which in a high-rate year look bad for doing exactly what they
    promised. ANBIMA publishes the IMA as a snapshot of the current day rather
    than as a series, so a window ending on a past date cannot be rebuilt from
    it. Affects 8% of the universe; see D-030.
    """
    return fund_return - benchmark_return


def annualised_volatility(returns: Series) -> float:
    """How much the fund moves day to day, expressed per year.

    Uses the sample standard deviation. For a year of daily data the choice
    between dividing by n and by n-1 moves the answer by 0.2% and changes no
    ranking; the annualisation factor, by contrast, moves it by 20%.
    """
    array = np.asarray(returns, dtype=np.float64)
    if array.size < 2:
        raise ValueError("volatility needs at least two returns")
    if not np.all(np.isfinite(array)):
        raise ValueError("return series contains missing or infinite values")
    return float(np.std(array, ddof=1) * np.sqrt(BUSINESS_DAYS_PER_YEAR))


def max_drawdown(quotas: Series) -> float:
    """The worst peak-to-trough fall in the period, as a negative number.

    Measured from the running peak, not from the start. A fund that doubled
    and then halved fell 50%, even though it ends above where it began — and
    the investor who bought at the top experienced exactly that.

    This is the risk number a client actually feels, which is why it carries
    weight in both profiles while plain volatility does not.
    """
    array = _as_quotas(quotas)
    running_peak = np.maximum.accumulate(array)
    return float(np.min(array / running_peak - 1.0))


def negative_day_share(returns: Series) -> float:
    """Share of days on which the fund lost money.

    A useful tell for credit funds: they post small positive returns almost
    every day, right up until they do not. A fund with an unusually low share
    here is not necessarily safe — it may simply not be marking its holdings.
    """
    array = np.asarray(returns, dtype=np.float64)
    if array.size == 0:
        raise ValueError("cannot compute a share of an empty series")
    return float(np.mean(array < 0))


def return_per_risk(fund_return: float, benchmark_return: float, volatility: float) -> float:
    """Excess return over the benchmark, per unit of volatility.

    Zero volatility is refused rather than treated as infinitely good. A fixed
    income fund whose quota does not move is not a miracle, it is a fund that
    has stopped being priced — and rewarding it would put exactly the wrong
    names at the top.
    """
    if volatility <= 0:
        raise ValueError(
            "return per unit of risk is undefined when volatility is zero; "
            "a quota that never moves is a pricing problem, not a good fund"
        )
    return excess_return(fund_return, benchmark_return) / volatility


def downside_volatility(returns: Series, threshold: float = 0.0) -> float:
    """Volatility of the losing days only.

    Upside movement is not risk. This separates the fund that is merely lively
    from the fund that actually hurts.
    """
    array = np.asarray(returns, dtype=np.float64)
    below = array[array < threshold]
    if below.size < 2:
        return 0.0
    return float(np.std(below, ddof=1) * np.sqrt(BUSINESS_DAYS_PER_YEAR))


def flow_stability(subscriptions: Series, redemptions: Series, average_assets: float) -> float:
    """Net flow over the period as a share of the fund's size.

    A fund bleeding redemptions is forced to sell whatever is easiest to sell,
    which degrades what is left for whoever stays. It is a forward-looking
    signal that the return series has not priced in yet.
    """
    if average_assets <= 0:
        raise ValueError("average net assets must be positive")
    inflow = np.asarray(subscriptions, dtype=np.float64)
    outflow = np.asarray(redemptions, dtype=np.float64)
    return float((np.nansum(inflow) - np.nansum(outflow)) / average_assets)
