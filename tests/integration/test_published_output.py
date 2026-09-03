"""Tests that read the delivered files, not the functions that wrote them.

Everything else in the suite checks a component against a fixture. That catches
a wrong formula and misses an entire class of defect: the machinery working
perfectly and the published answer still being wrong or misleading. A window
labelled with the wrong number of months, a top five holding one portfolio
twice, a weighted criterion that turns out to be a tie for every fund in the
pool — none of those break a function, and none of them show up in a green
suite that only ever looks inward.

So these open `ranking.json` and assert against the product.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from ranking import pipeline


@pytest.fixture(scope="module")
def payload(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("published")
    result = pipeline.run(
        reference_date=dt.date(2025, 12, 31),
        config_dir=Path(__file__).parents[2] / "configs",
        input_dir=Path(__file__).parents[1] / "fixtures",
        output_dir=output_dir,
        offline=True,
        lookback_months=3,
        simulations=50,
    )
    body = json.loads((result.output_dir / "ranking.json").read_text(encoding="utf-8"))
    body["_markdown"] = (result.output_dir / "ranking.md").read_text(encoding="utf-8")
    body["_comparison"] = (result.output_dir / "top10.md").read_text(encoding="utf-8")
    return body


# ---------------------------------------------------------------------------
# The window is what the label says
# ---------------------------------------------------------------------------


def test_the_published_window_matches_the_published_month_count(payload) -> None:
    start = dt.date.fromisoformat(payload["window_start"])
    end = dt.date.fromisoformat(payload["reference_date"])
    months = (end.year - start.year) * 12 + end.month - start.month + 1
    assert months == payload["lookback_months"]


def test_the_window_is_stated_in_dates_and_not_only_in_months(payload) -> None:
    """A month count cannot be checked by a reader. Two dates can."""
    start = dt.date.fromisoformat(payload["window_start"])
    assert f"{start:%d/%m/%Y}" in payload["_markdown"]


def test_the_readable_report_never_names_a_window_it_did_not_use(payload) -> None:
    months = payload["lookback_months"]
    wrong = {3, 6, 12, 24} - {months}
    for count in wrong:
        assert f"Rendeu em {count}m" not in payload["_markdown"]


# ---------------------------------------------------------------------------
# Five funds, not five scores
# ---------------------------------------------------------------------------


def test_no_fund_appears_twice_in_one_list(payload) -> None:
    for profile in payload["profiles"]:
        identifiers = [fund["cnpj_classe"] for fund in profile["top"]]
        assert len(identifiers) == len(set(identifiers))


def test_a_displaced_fund_names_what_it_duplicates_and_by_how_much(payload) -> None:
    """Passing a fund over is a decision the reader is entitled to audit, so it
    has to arrive with the fund it repeats and the distance between them."""
    for profile in payload["profiles"]:
        for item in profile["displaced"]:
            assert item["duplicate_of"]
            assert item["duplicate_of"] != item["name"]
            assert 0.0 <= item["tracking_difference"] <= 1.0


# ---------------------------------------------------------------------------
# Every weight does something
# ---------------------------------------------------------------------------


def test_the_weights_actually_applied_are_published(payload) -> None:
    for profile in payload["profiles"]:
        assert sum(profile["effective_weights"].values()) == 100


def test_an_inert_criterion_is_named_and_its_weight_moved_elsewhere(payload) -> None:
    """A metric every eligible fund ties on cannot separate anything, so its
    weight is redistributed rather than silently wasted — and the difference
    between declared and effective weights has to be visible."""
    for profile in payload["profiles"]:
        for metric in profile["inert_metrics"]:
            assert metric in profile["weights"]
            assert metric not in profile["effective_weights"]
        if not profile["inert_metrics"]:
            assert profile["effective_weights"] == profile["weights"]


# ---------------------------------------------------------------------------
# Nothing published is a placeholder
# ---------------------------------------------------------------------------


def test_every_peer_group_names_the_benchmark_it_was_measured_against(payload) -> None:
    """An empty benchmark field is worse than an absent one: it reads as though
    the question was asked and came back with nothing."""
    assert payload["benchmark_by_group"]
    assert all(payload["benchmark_by_group"].values())
    groups = {fund["peer_group"] for profile in payload["profiles"] for fund in profile["top"]}
    named = set(payload["benchmark_by_group"]) | {"(universo inteiro)"}
    assert groups <= named


def test_every_ranked_fund_states_its_tax_regime(payload) -> None:
    """Funds built on incentivised infrastructure debt are exempt for
    individuals, so 'before tax, relative order holds' is not true of every
    fund in the universe and the delivery must not imply that it is."""
    for profile in payload["profiles"]:
        for fund in profile["top"]:
            assert fund["metrics"]["regime_tributario"]


def test_each_fund_carries_both_the_peer_score_and_the_pool_score(payload) -> None:
    """A percentile inside a category says nothing about the category. Both
    numbers, or the reader cannot tell the best of a strong group from the best
    of a weak one."""
    for profile in payload["profiles"]:
        for fund in profile["top"]:
            assert 0 <= fund["score"] <= 100
            assert 0 <= fund["score_pool"] <= 100


def test_the_universe_a_profile_chose_from_is_described(payload) -> None:
    for profile in payload["profiles"]:
        assert profile["eligible_universe_size"] >= len(profile["top"])
        for share in profile["manager_share"].values():
            assert 0 < share <= 1


# ---------------------------------------------------------------------------
# The longer list never contradicts the delivered one
# ---------------------------------------------------------------------------


def test_the_comparison_list_opens_with_the_funds_that_were_delivered(payload) -> None:
    """A second, longer list published beside the answer is a liability the
    moment the two disagree. Both come from one walk down one ranked order, so
    the long one has to open with the short one, in the same order."""
    for profile in payload["profiles"]:
        section = payload["_comparison"].split(f"## {profile['label']}")[1]
        rows = [line for line in section.splitlines() if line.startswith("| ")][1:]
        for position, fund in enumerate(profile["top"], start=1):
            assert rows[position - 1].startswith(f"| {position} |")
            assert fund["name"][:44] in rows[position - 1]


def test_everything_past_the_delivered_five_is_marked_as_such(payload) -> None:
    """The delivery is five. A reader who takes the sixth name for a
    recommendation was misled by the file, not by their own carelessness."""
    delivered = payload["profiles"][0]["top_n"]
    for line in payload["_comparison"].splitlines():
        if not line.startswith("| ") or "Fundo" in line:
            continue
        rank = line.split("|")[1].strip()
        if rank.rstrip(" *").isdigit() and int(rank.rstrip(" *")) > delivered:
            assert rank.endswith("*")


# ---------------------------------------------------------------------------
# The cost gate actually holds on the delivered list
# ---------------------------------------------------------------------------


def test_no_published_fund_exceeds_the_cost_gate(payload) -> None:
    """D-051: the fee left the score and returns as a gate on the finalists, so
    no fund in a delivered list may sit above the ceiling. Each is judged by the
    reliable of its two fee figures, exactly as the pipeline judged it."""
    from ranking import config
    from ranking.transform import fees

    gate = config.load_profiles(Path(__file__).parents[2] / "configs" / "profiles.yaml").cost_gate
    for profile in payload["profiles"]:
        for fund in profile["top"]:
            numbers = fund["metrics"]
            cost = fees.gate_cost(
                numbers.get("taxa_adm_declarada"),
                numbers.get("taxa_adm_medida"),
                gate.declared_trusted_above,
            )
            assert cost is None or cost <= gate.max_annual_cost, fund["name"]


def test_no_published_fund_is_below_the_performance_floor(payload) -> None:
    """D-055: a fund beaten by most of its peers on excess return is struck,
    however cheap or long-lived. No delivered fund may sit below the floor."""
    from ranking import config

    floor = config.load_profiles(
        Path(__file__).parents[2] / "configs" / "profiles.yaml"
    ).selection.performance_floor
    for profile in payload["profiles"]:
        for fund in profile["top"]:
            pct = fund["percentiles"].get("excess_return")
            assert pct is None or pct >= floor, fund["name"]
