"""Whether a person can actually be inside the fund.

The delivery is a list for a retail individual, and the CVM's target-investor
field cannot support that claim: it says whether a fund is open to
non-qualified investors, not whether it admits a person rather than a company.
A class sold only to companies, pension schemes and insurers passes every
formal filter and is still not a product a person buys.

What settles it is not a clause but a count. The CVM publishes the shareholder
base of every class broken down by kind, so the question stops being "who is
allowed in" and becomes "who is in".
"""

from __future__ import annotations

import polars as pl

from ranking.transform import universe


def _profile(rows: list[tuple[str, float, float, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "cnpj_classe": [r[0] for r in rows],
            "cotistas_pf": [r[1] for r in rows],
            "cotistas_distribuidor": [r[2] for r in rows],
            "cotistas_pj": [r[3] for r in rows],
        },
        schema={
            "cnpj_classe": pl.Utf8,
            "cotistas_pf": pl.Float64,
            "cotistas_distribuidor": pl.Float64,
            "cotistas_pj": pl.Float64,
        },
    )


def _funds(ids: list[str]) -> pl.DataFrame:
    return pl.DataFrame({"cnpj_classe": ids}, schema={"cnpj_classe": pl.Utf8})


class TestReachableByAnIndividual:
    def test_a_class_holding_individuals_stays(self) -> None:
        out = universe.reachable_by_individuals(_funds(["A"]), _profile([("A", 1200.0, 0.0, 30.0)]))
        assert out["cnpj_classe"].to_list() == ["A"]

    def test_a_class_held_only_through_a_distributor_stays(self) -> None:
        """Money that arrives through a broker is reported as one distributor
        line rather than as the people behind it. Those people are exactly the
        retail investor this delivery is written for, so an opaque distributor
        line counts in favour of the fund, never against it."""
        out = universe.reachable_by_individuals(
            _funds(["A"]), _profile([("A", 0.0, 132_524.0, 14.0)])
        )
        assert out["cnpj_classe"].to_list() == ["A"]

    def test_a_class_with_no_individual_and_no_distributor_goes(self) -> None:
        """Companies, pension schemes and insurers only. Whatever the
        regulation permits, no person is inside, and the list is for a
        person."""
        out = universe.reachable_by_individuals(_funds(["A"]), _profile([("A", 0.0, 0.0, 6_476.0)]))
        assert out.is_empty()

    def test_a_class_with_no_profile_filed_is_kept(self) -> None:
        """Absence of the filing is not evidence of absence of people. The
        rule removes a fund only on positive evidence that no individual holds
        it, which is what keeps it from quietly deleting whatever the CVM
        happened not to publish that month."""
        out = universe.reachable_by_individuals(_funds(["A"]), _profile([]))
        assert out["cnpj_classe"].to_list() == ["A"]

    def test_the_rule_has_no_threshold_to_tune(self) -> None:
        """A single individual is enough. There is no cut-off to choose, and
        so no cut-off that could be chosen by looking at which funds it
        removes."""
        out = universe.reachable_by_individuals(
            _funds(["A", "B"]), _profile([("A", 1.0, 0.0, 9_000.0), ("B", 0.0, 0.0, 9_000.0)])
        )
        assert out["cnpj_classe"].to_list() == ["A"]

    def test_funds_keep_their_columns(self) -> None:
        funds = _funds(["A"]).with_columns(pl.lit(0.5).alias("taxa_adm"))
        out = universe.reachable_by_individuals(funds, _profile([("A", 5.0, 0.0, 0.0)]))
        assert set(out.columns) == {"cnpj_classe", "taxa_adm"}
