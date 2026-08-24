"""Five funds rather than five scores, and weights that do something.

Two rules shape the published list beyond the score itself: a criterion the
eligible pool ties on carries no information and its weight moves elsewhere,
and a fund that repeats one already on the list is passed over. Both change the
answer, so both are pinned here.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from ranking.rank import scoring, selection

# ---------------------------------------------------------------------------
# A metric everyone ties on cannot separate anyone
# ---------------------------------------------------------------------------


def test_dispersion_is_zero_when_every_fund_agrees() -> None:
    frame = pl.DataFrame({"dias_resgate": [0, 0, 0, 0, 0]})
    assert scoring.dispersion(frame, "dias_resgate") == 0.0


def test_dispersion_counts_the_funds_off_the_most_common_value() -> None:
    frame = pl.DataFrame({"dias_resgate": [0, 0, 0, 0, 1, 2]})
    assert scoring.dispersion(frame, "dias_resgate") == pytest.approx(2 / 6)


def test_dispersion_is_one_when_every_fund_differs() -> None:
    frame = pl.DataFrame({"taxa": [0.1, 0.2, 0.3, 0.4]})
    assert scoring.dispersion(frame, "taxa") == pytest.approx(0.75)


def test_nulls_do_not_count_as_a_shared_value() -> None:
    """A missing fee is not agreement about the fee."""
    frame = pl.DataFrame({"taxa": [0.1, 0.2, None, None]})
    assert scoring.dispersion(frame, "taxa") == pytest.approx(0.5)


def test_an_inert_metric_loses_its_weight_to_the_others() -> None:
    """The liquidity profile filters to same-day redemption and then weights
    redemption speed, which by then every fund ties on. The weight has to move
    rather than evaporate."""
    pool = pl.DataFrame(
        {
            "dias_resgate": [0] * 20,
            "admin_fee": [i / 100 for i in range(20)],
            "volatility": [i / 1000 for i in range(20)],
        }
    )
    weights = {"admin_fee": 30, "volatility": 20, "dias_resgate": 50}
    effective, inert = scoring.effective_weights(pool, weights, min_dispersion=0.05)

    assert inert == ["dias_resgate"]
    assert sum(effective.values()) == 100
    assert "dias_resgate" not in effective
    # 30 and 20 were three fifths and two fifths of what was left.
    assert effective == {"admin_fee": 60, "volatility": 40}


def test_weights_are_untouched_when_everything_discriminates() -> None:
    pool = pl.DataFrame({"a": list(range(10)), "b": list(range(10))})
    weights = {"a": 60, "b": 40}
    effective, inert = scoring.effective_weights(pool, weights, min_dispersion=0.05)
    assert inert == []
    assert effective == weights


def test_a_pool_where_nothing_discriminates_keeps_the_declared_weights() -> None:
    """Redistributing to nowhere would leave a score of zero for everyone. The
    declared weights are the honest fallback, and the ranking is meaningless
    either way — which the funnel and the universe size already say."""
    pool = pl.DataFrame({"a": [1] * 10, "b": [2] * 10})
    weights = {"a": 60, "b": 40}
    effective, inert = scoring.effective_weights(pool, weights, min_dispersion=0.05)
    assert effective == weights
    assert inert == []


# ---------------------------------------------------------------------------
# One portfolio, one slot
# ---------------------------------------------------------------------------


def test_the_ranking_order_is_never_rearranged() -> None:
    chosen, displaced = selection.pick_distinct(["a", "b", "c"], {}, top_n=3)
    assert chosen == ["a", "b", "c"]
    assert displaced == []


def test_a_twin_is_passed_over_and_the_next_fund_is_reached() -> None:
    duplicates = {"b": {"a": 0.0001}, "a": {"b": 0.0001}}
    chosen, displaced = selection.pick_distinct(["a", "b", "c", "d"], duplicates, top_n=3)

    assert chosen == ["a", "c", "d"]
    assert [item.cnpj_classe for item in displaced] == ["b"]
    assert displaced[0].duplicate_of == "a"


def test_being_a_twin_of_something_not_on_the_list_is_not_disqualifying() -> None:
    """`b` duplicates `z`, which never made the list. `b` is a perfectly good
    fifth name and there is no reason to skip it."""
    duplicates = {"b": {"z": 0.0001}}
    chosen, displaced = selection.pick_distinct(["a", "b"], duplicates, top_n=2)
    assert chosen == ["a", "b"]
    assert displaced == []


def test_the_closest_twin_is_the_one_reported() -> None:
    duplicates = {"c": {"a": 0.0009, "b": 0.0001}}
    _, displaced = selection.pick_distinct(["a", "b", "c", "d"], duplicates, top_n=3)
    assert displaced[0].duplicate_of == "b"


def test_a_fund_with_no_series_is_accepted_rather_than_rejected() -> None:
    """Absence of evidence that a fund duplicates something is not evidence
    that it does."""
    chosen, _ = selection.pick_distinct(["a", "unknown"], {"a": {"z": 0.0}}, top_n=2)
    assert chosen == ["a", "unknown"]


def test_a_whole_family_of_wrappers_collapses_to_one_slot() -> None:
    """Caixa runs a dozen distribution classes over one portfolio. The list
    should hold one of them, not five."""
    family = ["c1", "c2", "c3", "c4"]
    duplicates = {name: {other: 0.0002 for other in family if other != name} for name in family}
    chosen, displaced = selection.pick_distinct([*family, "other", "another"], duplicates, top_n=3)
    assert chosen == ["c1", "other", "another"]
    assert len(displaced) == 3


# ---------------------------------------------------------------------------
# The distance itself
# ---------------------------------------------------------------------------


def test_two_wrappers_of_one_portfolio_differ_only_by_a_constant() -> None:
    """The property the rule rests on: a fee is a constant daily drag, and a
    constant contributes no variance. Two share classes of one portfolio
    therefore have a tracking difference of essentially zero however much their
    fees differ."""
    rng = np.random.default_rng(0)
    portfolio = rng.normal(0.0005, 0.0002, 250)
    cheap = portfolio - 0.0004 / 252
    expensive = portfolio - 0.0150 / 252

    assert np.std(cheap - expensive) * np.sqrt(252) == pytest.approx(0.0, abs=1e-12)


class TestALongerListContainsTheShortOne:
    """The delivered five and the ten published for comparison come from one
    walk down the same ranked order, so the longer list is the shorter one plus
    what follows it. If that ever stopped being true, the comparison list would
    be describing a different ranking from the one delivered."""

    def test_the_first_five_of_ten_are_exactly_the_five(self) -> None:
        ordered = [f"f{i}" for i in range(20)]
        five, _ = selection.pick_distinct(ordered, {}, top_n=5)
        ten, _ = selection.pick_distinct(ordered, {}, top_n=10)
        assert ten[:5] == five
        assert len(ten) == 10

    def test_that_holds_when_duplicates_are_skipped_along_the_way(self) -> None:
        ordered = ["a", "a_twin", "b", "c", "c_twin", "d", "e", "f", "g", "h", "i", "j"]
        duplicates = {"a_twin": {"a": 0.0001}, "c_twin": {"c": 0.0002}}
        five, _ = selection.pick_distinct(ordered, duplicates, top_n=5)
        ten, _ = selection.pick_distinct(ordered, duplicates, top_n=10)
        assert ten[:5] == five
        assert "a_twin" not in ten and "c_twin" not in ten
