"""Financial invariants.

These are the tests that matter most. A wrong formula here does not crash and
does not look wrong — it just produces a confident, incorrect ranking. Every
test below states something that must be true no matter what the data is.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ranking.transform import metrics
from tests.conftest import EXPECTED, EXPECTED_CDI_COMPOUNDED

pytestmark = pytest.mark.invariant


# --------------------------------------------------------------------------
# Cumulative return
# --------------------------------------------------------------------------


def test_constant_quota_returns_zero() -> None:
    """A fund whose quota never moves earned nothing. Not 'almost nothing'."""
    assert metrics.cumulative_return([10.0] * 50) == pytest.approx(0.0, abs=1e-15)


def test_doubling_quota_returns_one_hundred_percent() -> None:
    assert metrics.cumulative_return([10.0, 15.0, 20.0]) == pytest.approx(1.0)


def test_cumulative_return_ignores_the_path() -> None:
    """Only the endpoints matter, however wild the ride in between."""
    calm = [100.0, 101.0, 102.0, 110.0]
    wild = [100.0, 300.0, 5.0, 110.0]
    assert metrics.cumulative_return(calm) == pytest.approx(metrics.cumulative_return(wild))


def test_daily_returns_compound_to_the_endpoint_return() -> None:
    """The single most valuable check: the day-by-day path must agree with the
    ends. Mixing simple and log returns silently breaks exactly this."""
    rng = np.random.default_rng(42)
    quotas = 100 * np.cumprod(1 + rng.normal(0.0004, 0.002, 500))

    compounded = np.prod(1 + metrics.daily_returns(quotas)) - 1
    endpoints = metrics.cumulative_return(quotas)

    assert compounded == pytest.approx(endpoints, rel=1e-12)


def test_series_shorter_than_two_points_is_rejected() -> None:
    """One observation is not a return. Refusing beats returning zero."""
    with pytest.raises(ValueError):
        metrics.cumulative_return([10.0])


def test_non_positive_quota_is_rejected() -> None:
    with pytest.raises(ValueError):
        metrics.cumulative_return([10.0, 0.0, 12.0])


# --------------------------------------------------------------------------
# Volatility
# --------------------------------------------------------------------------


def test_volatility_of_constant_series_is_zero() -> None:
    assert metrics.annualised_volatility(np.zeros(100)) == pytest.approx(0.0)


def test_volatility_is_never_negative() -> None:
    rng = np.random.default_rng(7)
    for _ in range(20):
        assert metrics.annualised_volatility(rng.normal(0, 0.01, 250)) >= 0


def test_volatility_annualises_with_252_business_days() -> None:
    """Fixed-income funds live on business days. Using 365 here would inflate
    every volatility by 20% and quietly reshuffle the whole ranking.

    Asserted as a ratio rather than an absolute, so that the test pins the
    annualisation factor — which is the thing that can be wrong — and stays
    silent about whether the estimator divides by n or by n-1, which moves the
    answer by 0.2% and changes no ranking.
    """
    rng = np.random.default_rng(5)
    daily = rng.normal(0, 0.01, 252)
    ratio = metrics.annualised_volatility(daily) / np.std(daily, ddof=1)
    assert ratio == pytest.approx(math.sqrt(252), rel=1e-9)


def test_volatility_scales_linearly_with_the_data() -> None:
    rng = np.random.default_rng(11)
    returns = rng.normal(0, 0.01, 300)
    doubled = metrics.annualised_volatility(returns * 2)
    assert doubled == pytest.approx(2 * metrics.annualised_volatility(returns), rel=1e-12)


# --------------------------------------------------------------------------
# Drawdown
# --------------------------------------------------------------------------


def test_drawdown_of_a_rising_series_is_zero() -> None:
    assert metrics.max_drawdown([1.0, 2.0, 3.0, 4.0]) == pytest.approx(0.0)


def test_drawdown_is_never_positive() -> None:
    rng = np.random.default_rng(3)
    for _ in range(20):
        quotas = 100 * np.cumprod(1 + rng.normal(0, 0.01, 200))
        assert metrics.max_drawdown(quotas) <= 0


def test_drawdown_known_value() -> None:
    """Up to 200, down to 150: a 25% fall from the peak."""
    assert metrics.max_drawdown([100.0, 200.0, 150.0, 180.0]) == pytest.approx(-0.25)


def test_drawdown_measures_from_the_peak_not_from_the_start() -> None:
    """A fund that rose then halved fell 50%, even though it ends above par."""
    assert metrics.max_drawdown([100.0, 400.0, 200.0]) == pytest.approx(-0.50)


# --------------------------------------------------------------------------
# Compounding the benchmark
# --------------------------------------------------------------------------


def test_compounding_is_multiplicative_not_additive() -> None:
    """1% a day for 100 days is 170.48%, not 100%. Summing rates is the classic
    way to overstate a low-rate benchmark and understate a high-rate one."""
    assert metrics.compound([0.01] * 100) == pytest.approx(1.01**100 - 1, rel=1e-12)
    assert metrics.compound([0.01] * 100) == pytest.approx(1.704814, rel=1e-6)


def test_compounding_an_empty_period_is_zero() -> None:
    assert metrics.compound([]) == pytest.approx(0.0)


def test_cdi_from_the_real_fixture(cdi_rates) -> None:
    """Verified against an independent calculation over the frozen CDI slice.

    `metrics` stays pure: the test reads the file, the module does the maths.
    """
    assert metrics.compound(cdi_rates) == pytest.approx(EXPECTED_CDI_COMPOUNDED, rel=1e-10)


# --------------------------------------------------------------------------
# Return per unit of risk
# --------------------------------------------------------------------------


def test_return_per_risk_uses_the_benchmark_not_zero() -> None:
    """A fund that returned exactly the benchmark added nothing, so its score
    is zero — however large the absolute return was."""
    assert metrics.return_per_risk(fund_return=0.12, benchmark_return=0.12, volatility=0.02) == 0.0


def test_return_per_risk_is_undefined_without_risk() -> None:
    """Zero volatility with excess return would be an infinite ratio. That is a
    data problem, not a great fund."""
    with pytest.raises(ValueError):
        metrics.return_per_risk(fund_return=0.13, benchmark_return=0.12, volatility=0.0)


def test_return_per_risk_known_value() -> None:
    assert metrics.return_per_risk(0.14, 0.12, 0.01) == pytest.approx(2.0)


# --------------------------------------------------------------------------
# Share of losing days
# --------------------------------------------------------------------------


def test_negative_day_share_bounds() -> None:
    assert metrics.negative_day_share(np.full(10, 0.001)) == 0.0
    assert metrics.negative_day_share(np.full(10, -0.001)) == 1.0


def test_flat_days_do_not_count_as_losses() -> None:
    assert metrics.negative_day_share(np.array([0.0, 0.0, -0.01, 0.01])) == pytest.approx(0.25)


# --------------------------------------------------------------------------
# Against the real fixture
# --------------------------------------------------------------------------


@pytest.mark.parametrize("cnpj", list(EXPECTED))
def test_period_return_matches_independent_calculation(cnpj: str, quota_series) -> None:
    """The number on the right was computed outside this code base, straight
    from the frozen CSV. If the implementation drifts, this catches it."""
    series = quota_series(cnpj)
    assert len(series) == EXPECTED[cnpj]["observations"]
    assert metrics.cumulative_return(series) == pytest.approx(
        EXPECTED[cnpj]["period_return"], rel=1e-9
    )


# --------------------------------------------------------------------------
# Downside volatility
# --------------------------------------------------------------------------


def test_upside_movement_is_not_risk() -> None:
    """A fund that only ever jumps upwards has no downside volatility, however
    lively it looks to a plain standard deviation."""
    only_gains = np.array([0.01, 0.05, 0.02, 0.09, 0.03])
    assert metrics.downside_volatility(only_gains) == 0.0
    assert metrics.annualised_volatility(only_gains) > 0


def test_downside_volatility_ignores_the_good_days() -> None:
    losses = np.array([-0.01, -0.02, -0.015])
    mixed = np.concatenate([losses, np.array([0.30, 0.40, 0.50])])
    assert metrics.downside_volatility(mixed) == pytest.approx(
        metrics.annualised_volatility(losses)
    )


def test_downside_volatility_is_never_negative() -> None:
    rng = np.random.default_rng(21)
    for _ in range(20):
        assert metrics.downside_volatility(rng.normal(0, 0.01, 200)) >= 0


def test_a_single_losing_day_is_not_enough_to_measure_spread() -> None:
    assert metrics.downside_volatility(np.array([0.01, 0.02, -0.01])) == 0.0


# --------------------------------------------------------------------------
# Flow stability
# --------------------------------------------------------------------------


def test_a_fund_taking_money_in_scores_positive() -> None:
    assert metrics.flow_stability([100.0, 50.0], [10.0, 5.0], average_assets=1_000.0) > 0


def test_a_fund_bleeding_redemptions_scores_negative() -> None:
    """The signal the return series has not priced in yet: a fund forced to
    sell whatever is easiest to sell degrades what is left for whoever stays."""
    assert metrics.flow_stability([10.0], [500.0], average_assets=1_000.0) < 0


def test_flow_stability_is_relative_to_size() -> None:
    """A hundred million leaving a billion-real fund is not the same event as a
    hundred million leaving a two-hundred-million one."""
    small = metrics.flow_stability([0.0], [100.0], average_assets=200.0)
    large = metrics.flow_stability([0.0], [100.0], average_assets=1_000.0)
    assert small < large


def test_flow_stability_known_value() -> None:
    assert metrics.flow_stability([300.0], [100.0], average_assets=1_000.0) == pytest.approx(0.2)


def test_flow_stability_refuses_a_fund_with_no_size() -> None:
    with pytest.raises(ValueError):
        metrics.flow_stability([1.0], [1.0], average_assets=0.0)


# --------------------------------------------------------------------------
# Excess return
# --------------------------------------------------------------------------


def test_beating_the_benchmark_is_positive() -> None:
    assert metrics.excess_return(0.14, 0.12) == pytest.approx(0.02)


def test_matching_the_benchmark_is_exactly_zero() -> None:
    assert metrics.excess_return(0.12, 0.12) == 0.0


def test_the_fixture_funds_both_lagged_the_cdi(quota_series, cdi_rates) -> None:
    """A real check on real numbers: both funds in the frozen slice returned
    less than the CDI over the quarter. If a change ever makes them look like
    they beat it, something in the chain moved."""
    benchmark = metrics.compound(cdi_rates)
    for cnpj in EXPECTED:
        fund = metrics.cumulative_return(quota_series(cnpj))
        assert metrics.excess_return(fund, benchmark) < 0
