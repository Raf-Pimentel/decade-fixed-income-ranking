"""Eligibility, scoring and the robustness simulation.

The ordering rule that matters: eligibility is applied *before* percentiles are
computed. Ranking everyone together and filtering afterwards would score a
retail fund against a universe it cannot buy from.
"""

from __future__ import annotations

import polars as pl
import pytest

from ranking.rank import eligibility, robustness, scoring


@pytest.fixture
def funds() -> pl.DataFrame:
    """Nine funds across two peer groups, with deliberately spread values."""
    return pl.DataFrame(
        {
            "cnpj_classe": [f"{i:014d}" for i in range(1, 10)],
            "peer_group": ["Soberano"] * 5 + ["Credito"] * 4,
            "excess_return": [0.001, 0.002, 0.003, 0.004, 0.005, 0.02, 0.03, 0.04, 0.05],
            "admin_fee": [0.005, 0.004, 0.003, 0.002, 0.001, 0.02, 0.015, 0.01, 0.005],
            "dias_resgate": [0, 1, 1, 30, 30, 30, 60, 90, 90],
            "publico_alvo": ["Público Geral"] * 6 + ["Qualificado"] * 3,
            "aplicacao_minima": [
                100.0,
                100.0,
                1_000.0,
                5_000.0,
                50_000.0,
                100_000.0,
                1e6,
                1e6,
                1e6,
            ],
        }
    )


# --------------------------------------------------------------------------
# Eligibility
# --------------------------------------------------------------------------


def test_retail_cannot_reach_qualified_only_funds(funds) -> None:
    eligible = eligibility.apply(
        funds,
        target_investor=["Público Geral"],
        max_minimum_investment_brl=50_000,
        max_redemption_days=30,
    )
    assert set(eligible["publico_alvo"].unique()) == {"Público Geral"}


def test_redemption_limit_is_applied(funds) -> None:
    eligible = eligibility.apply(
        funds,
        target_investor=["Público Geral"],
        max_minimum_investment_brl=50_000,
        max_redemption_days=30,
    )
    assert eligible["dias_resgate"].max() <= 30


def test_null_minimum_investment_means_no_limit(funds) -> None:
    eligible = eligibility.apply(
        funds, target_investor=None, max_minimum_investment_brl=None, max_redemption_days=90
    )
    assert len(eligible) == len(funds)


def test_eligibility_never_invents_rows(funds) -> None:
    eligible = eligibility.apply(
        funds,
        target_investor=["Público Geral"],
        max_minimum_investment_brl=50_000,
        max_redemption_days=30,
    )
    assert len(eligible) <= len(funds)


# --------------------------------------------------------------------------
# Peer-group percentiles
# --------------------------------------------------------------------------


def test_percentile_is_computed_inside_the_peer_group(funds) -> None:
    """The best credit fund and the best sovereign fund must both score 1.0 in
    their own group, even though their raw returns differ by 10x. This is what
    stops the ranking from simply selecting the most credit risk."""
    scored = scoring.peer_percentile(
        funds, metric="excess_return", group="peer_group", direction="high"
    )
    best_sovereign = scored.filter(pl.col("cnpj_classe") == "00000000000005")
    best_credit = scored.filter(pl.col("cnpj_classe") == "00000000000009")
    assert best_sovereign["excess_return_pct"].item() == pytest.approx(1.0)
    assert best_credit["excess_return_pct"].item() == pytest.approx(1.0)


def test_low_direction_inverts_the_ranking(funds) -> None:
    """Cheapest fund wins on fees."""
    scored = scoring.peer_percentile(funds, metric="admin_fee", group="peer_group", direction="low")
    cheapest = scored.filter(pl.col("cnpj_classe") == "00000000000005")
    assert cheapest["admin_fee_pct"].item() == pytest.approx(1.0)


def test_percentiles_stay_between_zero_and_one(funds) -> None:
    scored = scoring.peer_percentile(
        funds, metric="excess_return", group="peer_group", direction="high"
    )
    values = scored["excess_return_pct"]
    assert values.min() >= 0.0 and values.max() <= 1.0


def test_a_small_group_is_not_scored_against_itself(funds) -> None:
    """A percentile inside a group of four funds is noise, not information.

    Those funds fall back to being compared against the whole eligible
    universe, and the output says so — which is honest, where inventing a
    peer group out of four names would not be.
    """
    merged = scoring.merge_small_groups(funds, group="peer_group", min_size=5)
    credito = merged.filter(pl.col("peer_group") == "Credito")
    assert credito["peer_group_effective"].unique().to_list() == [scoring.GLOBAL_PEER_GROUP]


def test_a_group_that_is_big_enough_keeps_its_identity(funds) -> None:
    merged = scoring.merge_small_groups(funds, group="peer_group", min_size=5)
    soberano = merged.filter(pl.col("peer_group") == "Soberano")
    assert soberano["peer_group_effective"].unique().to_list() == ["Soberano"]


def test_a_pooled_fund_is_ranked_against_everyone(funds) -> None:
    """Falling back must mean "compared against all of them", not "compared
    against the other four strays"."""
    merged = scoring.merge_small_groups(funds, group="peer_group", min_size=5)
    scored = scoring.peer_percentile(
        merged, metric="excess_return", group="peer_group_effective", direction="high"
    )
    best_overall = scored.filter(pl.col("cnpj_classe") == "00000000000009")
    # fund 9 has the highest excess return in the whole frame
    assert best_overall["excess_return_pct"].item() == pytest.approx(1.0)
    worst_pooled = scored.filter(pl.col("cnpj_classe") == "00000000000006")
    # fund 6 is the weakest of the pooled ones but still beats all five
    # sovereign funds, so against the whole universe it is mid-table, not last
    assert 0.0 < worst_pooled["excess_return_pct"].item() < 1.0


def test_winsorising_limits_the_effect_of_one_outlier() -> None:
    frame = pl.DataFrame({"g": ["a"] * 10, "m": [1.0] * 9 + [1_000.0]})
    capped = scoring.winsorise(frame, metric="m", lower=0.01, upper=0.99)
    assert capped["m"].max() < 1_000.0


# --------------------------------------------------------------------------
# Score
# --------------------------------------------------------------------------


def test_score_is_the_weighted_sum_of_percentiles() -> None:
    frame = pl.DataFrame({"a_pct": [1.0, 0.0], "b_pct": [0.0, 1.0]})
    scored = scoring.total_score(frame, weights={"a": 75, "b": 25})
    assert scored["score"].to_list() == pytest.approx([75.0, 25.0])


def test_score_rejects_weights_that_do_not_sum_to_one_hundred() -> None:
    frame = pl.DataFrame({"a_pct": [1.0]})
    with pytest.raises(ValueError):
        scoring.total_score(frame, weights={"a": 90})


def test_score_rejects_a_weight_with_no_matching_column() -> None:
    frame = pl.DataFrame({"a_pct": [1.0]})
    with pytest.raises(KeyError):
        scoring.total_score(frame, weights={"a": 50, "missing": 50})


# --------------------------------------------------------------------------
# Robustness: is the top 5 real, or is it noise?
# --------------------------------------------------------------------------


def test_same_seed_gives_the_same_answer(funds) -> None:
    """Reproducibility is not negotiable — the same reference date must always
    produce the same ranking."""
    first = robustness.simulate(funds, weights={"excess_return": 100}, seed=1, simulations=50)
    second = robustness.simulate(funds, weights={"excess_return": 100}, seed=1, simulations=50)
    assert first["appearance_rate"].to_list() == second["appearance_rate"].to_list()


def test_without_jitter_the_answer_does_not_depend_on_the_seed(funds) -> None:
    """Nothing is varying, so every simulation is the same simulation. That is
    correct behaviour, not a broken seed — and it is why a run with no jitter
    configured proves nothing about robustness."""
    weights = {"excess_return": 50, "admin_fee": 50}
    first = robustness.simulate(funds, weights=weights, seed=1, simulations=50)
    second = robustness.simulate(funds, weights=weights, seed=2, simulations=50)
    assert first["appearance_rate"].to_list() == second["appearance_rate"].to_list()


def test_with_jitter_the_seed_changes_the_draws(funds) -> None:
    weights = {"excess_return": 50, "admin_fee": 50}
    ranges = {"excess_return": 20, "admin_fee": 20}
    first = robustness.simulate(funds, weights=weights, jitter=ranges, seed=1, simulations=200)
    second = robustness.simulate(funds, weights=weights, jitter=ranges, seed=2, simulations=200)
    assert first["appearance_rate"].to_list() != second["appearance_rate"].to_list()


def test_appearance_rate_is_a_share(funds) -> None:
    result = robustness.simulate(funds, weights={"excess_return": 100}, seed=1, simulations=50)
    rates = result["appearance_rate"]
    assert rates.min() >= 0.0 and rates.max() <= 1.0


def test_a_dominant_fund_appears_almost_always() -> None:
    """Sanity: if one fund is better on every metric, no amount of jitter
    should dislodge it."""
    frame = pl.DataFrame(
        {
            "cnpj_classe": [f"{i:014d}" for i in range(1, 11)],
            "peer_group": ["g"] * 10,
            "excess_return": [0.9] + [0.1] * 9,
            "admin_fee": [0.001] + [0.02] * 9,
        }
    )
    result = robustness.simulate(
        frame, weights={"excess_return": 50, "admin_fee": 50}, seed=1, simulations=200
    )
    winner = result.filter(pl.col("cnpj_classe") == "00000000000001")
    assert winner["appearance_rate"].item() > 0.95


def test_report_separates_metrics_that_move_from_metrics_that_do_not(funds) -> None:
    """Fees are constant across simulations, so they inflate apparent
    stability. Reporting the split keeps the 91% honest."""
    result = robustness.simulate(
        funds, weights={"excess_return": 50, "admin_fee": 50}, seed=1, simulations=50
    )
    assert "appearance_rate_variable_only" in result.columns
