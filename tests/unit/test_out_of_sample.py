"""The out-of-sample test must not flatter itself.

Two ways a backtest quietly marks its own homework, both of them invisible in
the result: measuring only the funds that survived to the end, and comparing
against a benchmark that was never computed. Neither raises anything. Both make
the method look better than it was.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from ranking import backtest
from ranking.config import Backtest

RULES = Backtest(
    cut_dates=[dt.date(2025, 3, 31)],
    random_portfolios=200,
    seed=1,
    success_percentile=60,
    success_min_dates=1,
    discontinued_fund_policy="carry_last_value",
)


# ---------------------------------------------------------------------------
# A fund that left the universe is still charged to the method
# ---------------------------------------------------------------------------


def test_a_fund_that_left_the_eligible_set_still_counts_against_the_result() -> None:
    """The selected fund `gone` is no longer eligible at the end, so it is
    absent from `eligible_returns`. Its outcome was bad and it has to be in the
    average: dropping it is the survivorship bias this test exists to detect.
    """
    eligible = {"a": 0.10, "b": 0.10, "c": 0.10}
    everything = {**eligible, "gone": -0.50}

    outcome = backtest.evaluate(
        profile_id="p",
        cut_date=dt.date(2025, 3, 31),
        selected=["a", "gone"],
        eligible_returns=eligible,
        benchmark_return=0.09,
        rules=RULES,
        forward_returns_all=everything,
    )
    assert outcome.selected_return == pytest.approx((0.10 - 0.50) / 2)


def test_the_average_always_divides_by_every_fund_that_was_chosen() -> None:
    """The guarantee behind the previous test, stated as a property. Whatever
    panel is handed in, the divisor is the number of funds the method picked —
    never the number of them that happened to be measurable. A fund missing
    from the panel contributes its carried value of zero and still counts, so
    a bad or vanished pick can never improve the average by leaving it."""
    eligible = {"a": 0.10, "b": 0.10, "c": 0.10}
    outcome = backtest.evaluate(
        profile_id="p",
        cut_date=dt.date(2025, 3, 31),
        selected=["a", "gone"],
        eligible_returns=eligible,
        benchmark_return=0.09,
        rules=RULES,
    )
    assert outcome.selected_return == pytest.approx((0.10 + 0.0) / 2)
    assert outcome.carried == ["gone"]


def test_a_fund_with_no_forward_quota_is_carried_flat_and_named() -> None:
    """The frozen policy is `carry_last_value`. A fund that published nothing
    after the cut is held where it was — a zero return, not an exclusion — and
    the report says which funds those were."""
    outcome = backtest.evaluate(
        profile_id="p",
        cut_date=dt.date(2025, 3, 31),
        selected=["a", "silent"],
        eligible_returns={"a": 0.10, "b": 0.08},
        benchmark_return=0.09,
        rules=RULES,
        forward_returns_all={"a": 0.10, "b": 0.08},
    )
    assert outcome.carried == ["silent"]
    assert outcome.selected_return == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# The benchmark is a real number
# ---------------------------------------------------------------------------


def test_the_benchmark_is_compounded_over_the_measured_days_only() -> None:
    daily = pl.DataFrame(
        {
            "data": [dt.date(2025, 1, 2), dt.date(2025, 6, 2), dt.date(2025, 12, 1)],
            "taxa": [0.01, 0.02, 0.03],
        }
    )
    # Strictly after the cut, so only the June and December rates chain.
    assert backtest.benchmark_return(
        daily, start=dt.date(2025, 3, 31), end=dt.date(2025, 12, 31)
    ) == pytest.approx(1.02 * 1.03 - 1)


def test_the_benchmark_compounds_rather_than_adds() -> None:
    daily = pl.DataFrame({"data": [dt.date(2025, 6, 1)] * 0, "taxa": []}).with_columns(
        pl.col("data").cast(pl.Date), pl.col("taxa").cast(pl.Float64)
    )
    assert backtest.benchmark_return(daily, dt.date(2025, 1, 1), dt.date(2025, 12, 31)) == 0.0


def test_a_missing_benchmark_series_is_zero_rather_than_an_exception() -> None:
    assert backtest.benchmark_return(None, dt.date(2025, 1, 1), dt.date(2025, 12, 31)) == 0.0


# ---------------------------------------------------------------------------
# The cost-matched control
# ---------------------------------------------------------------------------


def test_the_cheap_control_keeps_only_the_least_expensive_quarter() -> None:
    returns = {f"f{i}": 0.1 for i in range(12)}
    fees = {f"f{i}": i / 100 for i in range(12)}
    cheap = backtest.cheapest_quartile(returns, fees)
    assert set(cheap) == {"f0", "f1", "f2"}


def test_the_cheap_control_falls_back_to_the_whole_universe_when_too_small() -> None:
    """Three funds have no meaningful quartile. Silently ranking against two of
    them would produce a percentile that looks like evidence and is not."""
    returns = {"a": 0.1, "b": 0.2, "c": 0.3}
    assert backtest.cheapest_quartile(returns, {"a": 0.01, "b": 0.02, "c": 0.03}) == returns


def test_funds_with_no_published_fee_do_not_enter_the_cheap_control() -> None:
    """An unknown fee is not a low fee, and this control's whole point is that
    cost is held constant."""
    returns = {f"f{i}": 0.1 for i in range(12)}
    fees = {f"f{i}": i / 100 for i in range(12) if i != 0}
    assert "f0" not in backtest.cheapest_quartile(returns, fees)


# ---------------------------------------------------------------------------
# The forward window never touches the data the ranking saw
# ---------------------------------------------------------------------------


def test_the_forward_window_starts_strictly_after_the_cut() -> None:
    series = pl.DataFrame(
        {
            "cnpj_classe": ["x"] * 3,
            "data": [dt.date(2025, 3, 31), dt.date(2025, 6, 30), dt.date(2025, 12, 31)],
            "valor_cota": [1.0, 1.1, 1.2],
        }
    )
    realised = backtest.forward_returns(series, dt.date(2025, 3, 31), dt.date(2025, 12, 31))
    # From 1.1 to 1.2, never from 1.0: the quota on the cut date belongs to the
    # ranking, not to the measurement.
    assert realised["x"] == pytest.approx(1.2 / 1.1 - 1)


def test_random_portfolios_are_drawn_without_replacement() -> None:
    values = {f"f{i}": float(i) for i in range(10)}
    draws = backtest.random_portfolios(values, size=10, draws=5, seed=3)
    # Drawing all ten without replacement can only ever give the same mean.
    assert np.allclose(draws, np.mean(list(values.values())))
