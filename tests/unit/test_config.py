"""The configuration files are part of the contract, so they get tested too.

Nothing that decides the ranking may live in code. If a weight, a cut-off or a
window is hard-coded somewhere, these tests are the ones that should have
caught it.
"""

from __future__ import annotations

import pytest

from ranking import config


@pytest.fixture
def profiles(config_dir):
    return config.load_profiles(config_dir / "profiles.yaml")


@pytest.fixture
def universe(config_dir):
    return config.load_universe(config_dir / "universe.yaml")


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------


def test_both_profiles_exist(profiles) -> None:
    """Two retail profiles, split by horizon. See decision D-032."""
    assert set(profiles.profiles) == {"varejo_liquidez", "varejo_prazo"}


@pytest.mark.parametrize("profile_id", ["varejo_liquidez", "varejo_prazo"])
def test_weights_sum_to_one_hundred(profiles, profile_id: str) -> None:
    assert sum(profiles.profiles[profile_id].weights.values()) == 100


@pytest.mark.parametrize("profile_id", ["varejo_liquidez", "varejo_prazo"])
def test_every_weight_refers_to_a_declared_metric(profiles, profile_id: str) -> None:
    unknown = set(profiles.profiles[profile_id].weights) - set(profiles.metrics)
    assert not unknown, f"weights refer to undeclared metrics: {unknown}"


@pytest.mark.parametrize("profile_id", ["varejo_liquidez", "varejo_prazo"])
def test_jitter_only_covers_weights_that_exist(profiles, profile_id: str) -> None:
    profile = profiles.profiles[profile_id]
    assert set(profile.jitter) <= set(profile.weights)


def test_every_metric_declares_a_direction(profiles) -> None:
    """Without a direction, "higher percentile is better" is meaningless and a
    low-cost fund would be ranked as if expensive were good."""
    for name, metric in profiles.metrics.items():
        assert metric.direction in {"high", "low"}, name


@pytest.mark.parametrize("profile_id", ["varejo_liquidez", "varejo_prazo"])
def test_cost_outweighs_past_return_in_both_profiles(profiles, profile_id: str) -> None:
    """Decision D-012, encoded so that it cannot be quietly reversed: the fee is
    the only number we actually know about next year, and only 37% of funds beat
    the CDI in 2025."""
    weights = profiles.profiles[profile_id].weights
    assert weights["admin_fee"] > weights["excess_return"]


def test_the_fee_is_the_single_largest_weight(profiles) -> None:
    for profile in profiles.profiles.values():
        heaviest = max(profile.weights, key=lambda name: profile.weights[name])
        assert heaviest == "admin_fee", profile.label


def test_the_liquidity_profile_is_the_stricter_one(profiles) -> None:
    """The horizon profile can buy everything the liquidity one can, and more.
    Spare liquidity is not a defect."""
    liquidez = profiles.profiles["varejo_liquidez"].eligibility
    prazo = profiles.profiles["varejo_prazo"].eligibility
    assert liquidez.max_redemption_days < prazo.max_redemption_days


# --------------------------------------------------------------------------
# The backtest criteria are frozen before the backtest runs
# --------------------------------------------------------------------------


def test_backtest_criteria_are_declared_up_front(profiles) -> None:
    """Rule 11 in CLAUDE.md. These values are committed and dated; changing
    them after seeing a result would show up in the git history."""
    backtest = profiles.backtest
    assert len(backtest.cut_dates) == 3
    assert backtest.success_percentile == 60
    assert backtest.success_min_dates == 2
    assert backtest.discontinued_fund_policy == "carry_last_value"


def test_robustness_uses_a_fixed_seed(profiles) -> None:
    assert profiles.robustness.seed is not None
    assert profiles.robustness.simulations >= 1000


def test_robustness_reports_which_metrics_actually_vary(profiles) -> None:
    """Fees do not move between simulations, so they inflate apparent
    stability. The report must separate the two."""
    assert profiles.robustness.report_split_by_variability is True


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------


def test_universe_requires_fee_and_redemption(universe) -> None:
    assert universe.filters.require_fee_and_redemption is True


def test_expected_funnel_is_monotonically_decreasing(universe) -> None:
    """A funnel step that grows means the filters are in the wrong order."""
    counts = list(universe.expected_funnel.steps.values())
    assert counts == sorted(counts, reverse=True)


def test_expected_funnel_matches_what_was_measured(universe) -> None:
    steps = universe.expected_funnel.steps
    assert steps["registered_classes"] == 36_594  # distinct, after collapsing 4 duplicates
    assert steps["above_min_shareholders"] == 787
    assert steps["with_fee_and_redemption"] == 580


def test_lookback_window_is_configurable_not_hard_coded(universe) -> None:
    assert universe.lookback_months == 12
    assert 12 in universe.report_windows


def test_peer_groups_have_a_minimum_size(universe) -> None:
    """Percentiles inside a group of eight funds are noise."""
    assert universe.peer_groups.min_size >= 20


def test_benchmarks_are_not_all_cdi(universe) -> None:
    """Decision D-014: judging an inflation-linked fund against CDI is wrong."""
    assert set(universe.peer_groups.benchmarks.values()) > {"CDI"}
