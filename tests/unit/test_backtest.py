"""Does the method work, or is it only defensible?

Everything here answers one question: if the ranking had been built at some
earlier date, would the five funds it chose have done better than the
alternatives an investor actually had?

The criteria live in configuration and were committed before this ran. The
tests below check that the code reads them from there rather than carrying its
own copy — a hard-coded threshold is a threshold that can be quietly moved.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from ranking import backtest
from ranking.config import load_profiles

CUT = dt.date(2025, 6, 30)
END = dt.date(2025, 12, 31)


def _series(rows: dict[str, list[float]], start: dt.date = dt.date(2025, 7, 1)) -> pl.DataFrame:
    frames = []
    for cnpj, quotas in rows.items():
        frames.append(
            pl.DataFrame(
                {
                    "cnpj_classe": [cnpj] * len(quotas),
                    "data": [start + dt.timedelta(days=index) for index in range(len(quotas))],
                    "valor_cota": quotas,
                }
            )
        )
    return pl.concat(frames)


# --------------------------------------------------------------------------
# What each fund did after the cut
# --------------------------------------------------------------------------


def test_forward_return_is_measured_after_the_cut_only() -> None:
    """The whole exercise is worthless if a single pre-cut day leaks in."""
    series = _series({"a": [100.0, 110.0]}, start=dt.date(2025, 6, 1))
    forward = backtest.forward_returns(series, start=CUT, end=END)
    assert forward == {}, "days before the cut must not count"


def test_a_fund_that_doubled_shows_one_hundred_percent() -> None:
    forward = backtest.forward_returns(_series({"a": [100.0, 150.0, 200.0]}), start=CUT, end=END)
    assert forward["a"] == pytest.approx(1.0)


def test_a_fund_that_stops_reporting_is_carried_at_its_last_value() -> None:
    """Frozen before running, in configuration. Dropping the fund instead would
    be the survivorship bias this project criticises, applied to itself: the
    one that vanished is exactly the one you want counted."""
    series = _series({"alive": [100.0] * 184, "gone": [100.0, 101.0, 102.0]})
    forward = backtest.forward_returns(series, start=CUT, end=END)
    assert forward["gone"] == pytest.approx(0.02)


def test_discontinued_funds_are_named() -> None:
    # "alive" runs to the end of the window; "gone" stops in July.
    series = _series({"alive": [100.0] * 184, "gone": [100.0, 101.0]})
    stopped = backtest.discontinued(series, end=END, tolerance_days=30)
    assert stopped == ["gone"]


# --------------------------------------------------------------------------
# The control that matters: did we beat chance?
# --------------------------------------------------------------------------


def test_a_random_portfolio_is_the_average_of_its_members() -> None:
    returns = {"a": 0.10, "b": 0.20, "c": 0.30, "d": 0.40, "e": 0.50}
    draws = backtest.random_portfolios(returns, size=5, draws=10, seed=1)
    assert np.allclose(draws, 0.30)


def test_random_portfolios_are_reproducible() -> None:
    returns = {chr(97 + index): index / 100 for index in range(30)}
    first = backtest.random_portfolios(returns, size=5, draws=100, seed=7)
    second = backtest.random_portfolios(returns, size=5, draws=100, seed=7)
    assert np.array_equal(first, second)


def test_the_percentile_says_how_much_of_chance_we_beat() -> None:
    draws = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
    assert backtest.percentile_of(0.35, draws) == pytest.approx(0.80)
    assert backtest.percentile_of(-1.0, draws) == pytest.approx(0.0)
    assert backtest.percentile_of(9.9, draws) == pytest.approx(1.0)


def test_beating_only_half_of_chance_is_the_fiftieth_percentile() -> None:
    draws = np.arange(0.0, 1.0, 0.01)
    assert backtest.percentile_of(0.5, draws) == pytest.approx(0.5, abs=0.02)


# --------------------------------------------------------------------------
# The verdict, read from configuration
# --------------------------------------------------------------------------


def _outcome(percentile: float, cut: dt.date) -> backtest.Outcome:
    return backtest.Outcome(
        cut_date=cut,
        profile_id="varejo_prazo",
        selected=["a"],
        selected_return=0.1,
        peer_median_return=0.05,
        benchmark_return=0.04,
        random_percentile=percentile,
        beat_median=3,
        discontinued=[],
    )


def test_two_of_three_above_the_threshold_passes(config_dir) -> None:
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = [
        _outcome(0.75, dt.date(2025, 3, 31)),
        _outcome(0.65, dt.date(2025, 6, 30)),
        _outcome(0.20, dt.date(2025, 9, 30)),
    ]
    assert backtest.verdict(outcomes, rules).passed


def test_one_of_three_fails(config_dir) -> None:
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = [
        _outcome(0.75, dt.date(2025, 3, 31)),
        _outcome(0.30, dt.date(2025, 6, 30)),
        _outcome(0.10, dt.date(2025, 9, 30)),
    ]
    assert not backtest.verdict(outcomes, rules).passed


def test_exactly_at_the_threshold_does_not_count(config_dir) -> None:
    """Above the sixtieth percentile means above it."""
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = [_outcome(0.60, dt.date(2025, 3, 31)), _outcome(0.60, dt.date(2025, 6, 30))]
    assert not backtest.verdict(outcomes, rules).passed


def test_the_threshold_is_read_from_configuration_not_hard_coded(config_dir) -> None:
    """A criterion the code carries its own copy of is a criterion that can be
    moved without anyone noticing. This one is committed and dated."""
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    assert rules.success_percentile == 60
    assert rules.success_min_dates == 2
    strict = rules.model_copy(update={"success_percentile": 99})
    outcomes = [_outcome(0.75, dt.date(2025, 3, 31)), _outcome(0.65, dt.date(2025, 6, 30))]
    assert backtest.verdict(outcomes, rules).passed
    assert not backtest.verdict(outcomes, strict).passed


def test_the_verdict_reports_which_dates_passed(config_dir) -> None:
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = [_outcome(0.75, dt.date(2025, 3, 31)), _outcome(0.10, dt.date(2025, 6, 30))]
    result = backtest.verdict(outcomes, rules)
    assert result.dates_passed == 1
    assert result.dates_tested == 2


# --------------------------------------------------------------------------
# The criterion is per profile, not pooled
# --------------------------------------------------------------------------


def _for(profile: str, percentiles: list[float]) -> list[backtest.Outcome]:
    dates = [dt.date(2025, 3, 31), dt.date(2025, 6, 30), dt.date(2025, 9, 30)]
    return [
        backtest.Outcome(
            cut_date=date,
            profile_id=profile,
            selected=["a"],
            selected_return=0.1,
            peer_median_return=0.05,
            benchmark_return=0.04,
            random_percentile=percentile,
            beat_median=3,
            discontinued=[],
        )
        for date, percentile in zip(dates, percentiles, strict=True)
    ]


def test_pooling_profiles_would_make_the_criterion_easier(config_dir) -> None:
    """Two profiles across three dates give six results. Requiring two of six
    is a far weaker claim than requiring two of three for each profile, and the
    frozen criterion speaks of dates. Every profile must clear it on its own.
    """
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = _for("varejo_liquidez", [0.9, 0.9, 0.9]) + _for("varejo_prazo", [0.1, 0.1, 0.1])
    assert not backtest.verdict(outcomes, rules).passed


def test_every_profile_must_clear_the_bar(config_dir) -> None:
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = _for("varejo_liquidez", [0.92, 1.0, 0.98]) + _for("varejo_prazo", [0.84, 0.97, 0.51])
    result = backtest.verdict(outcomes, rules)
    assert result.passed
    assert result.by_profile["varejo_liquidez"] == 3
    assert result.by_profile["varejo_prazo"] == 2


def test_a_profile_failing_two_of_three_sinks_the_verdict(config_dir) -> None:
    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes = _for("varejo_liquidez", [0.9, 0.9, 0.9]) + _for("varejo_prazo", [0.9, 0.3, 0.3])
    assert not backtest.verdict(outcomes, rules).passed
