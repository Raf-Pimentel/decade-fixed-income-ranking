"""Measuring what a fund charges instead of reading what it declared.

The administration fee is the heaviest weight in both profiles, and for a
whole family of classes the filed value is not the price the client pays. A
feeder class puts nearly all of its money into one master fund, so the two
quota series are the same portfolio and the only thing separating them is what
the class charges. That difference is measurable, and it does not depend on
anyone filling a form correctly.
"""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from ranking.transform import fees


def _series(cnpj: str, values: list[float], start: dt.date = dt.date(2025, 1, 2)) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "cnpj_classe": [cnpj] * len(values),
            "data": [start + dt.timedelta(days=i) for i in range(len(values))],
            "valor_cota": values,
        }
    )


def _holdings(rows: list[tuple[str, str, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "cnpj_classe": [r[0] for r in rows],
            "cnpj_investido": [r[1] for r in rows],
            "valor": [r[2] for r in rows],
        },
        schema={"cnpj_classe": pl.Utf8, "cnpj_investido": pl.Utf8, "valor": pl.Float64},
    )


class TestMasterOf:
    def test_a_class_that_holds_one_fund_outright_has_that_fund_as_its_master(self) -> None:
        links = fees.master_of(_holdings([("A", "M", 100.0)]), min_share=0.95)
        assert links.to_dicts() == [{"cnpj_classe": "A", "cnpj_master": "M", "share": 1.0}]

    def test_a_small_cash_sleeve_does_not_stop_the_master_being_identified(self) -> None:
        """Feeders park a little in an overnight fund. Demanding a perfect 100%
        would throw away almost every real case."""
        links = fees.master_of(_holdings([("A", "M", 99.0), ("A", "Z", 1.0)]), min_share=0.95)
        assert links["cnpj_master"].to_list() == ["M"]

    def test_a_class_spread_across_funds_has_no_master(self) -> None:
        """Half in one fund and half in another is a portfolio of funds, not a
        wrapper. The difference in returns would carry allocation as well as
        cost, and would not be a fee."""
        links = fees.master_of(_holdings([("A", "M", 50.0), ("A", "N", 50.0)]), min_share=0.95)
        assert links.is_empty()

    def test_the_threshold_is_the_caller_decision_not_a_hidden_constant(self) -> None:
        holdings = _holdings([("A", "M", 90.0), ("A", "Z", 10.0)])
        assert fees.master_of(holdings, min_share=0.95).is_empty()
        assert fees.master_of(holdings, min_share=0.85)["cnpj_master"].to_list() == ["M"]


class TestMeasuredFee:
    def test_a_class_that_tracks_its_master_exactly_charges_nothing(self) -> None:
        panel = pl.concat([_series("A", [1.0, 1.1, 1.2]), _series("M", [2.0, 2.2, 2.4])])
        links = pl.DataFrame({"cnpj_classe": ["A"], "cnpj_master": ["M"]})
        out = fees.measured(panel, links, business_days_per_year=252, min_overlap_days=2)
        assert out["taxa_adm_medida"].to_list() == pytest.approx([0.0], abs=1e-12)

    def test_the_class_keeps_a_fraction_of_the_master_and_that_fraction_is_the_fee(self) -> None:
        """A master that grows 10% over a business year, wrapped by a class
        charging 1%, leaves the client with 1.10 x 0.99."""
        days = 252
        master = [1.10 ** (i / days) for i in range(days + 1)]
        feeder = [(1.10 * 0.99) ** (i / days) for i in range(days + 1)]
        panel = pl.concat([_series("A", feeder), _series("M", master)])
        links = pl.DataFrame({"cnpj_classe": ["A"], "cnpj_master": ["M"]})
        out = fees.measured(panel, links, business_days_per_year=days)
        assert out["taxa_adm_medida"].item() == pytest.approx(0.01, abs=1e-9)

    def test_the_same_fee_measures_the_same_however_long_the_window_is(self) -> None:
        """A fee is charged day after day, so it compounds. Annualising the
        plain difference in returns would make the same fund look cheaper on a
        short history and dearer on a long one, and the funds with the shortest
        history are exactly the ones already hardest to judge."""

        def rate(days: int) -> float:
            master = [1.10 ** (i / 252) for i in range(days + 1)]
            feeder = [(1.10 * 0.99) ** (i / 252) for i in range(days + 1)]
            panel = pl.concat([_series("A", feeder), _series("M", master)])
            links = pl.DataFrame({"cnpj_classe": ["A"], "cnpj_master": ["M"]})
            return fees.measured(panel, links, business_days_per_year=252)["taxa_adm_medida"].item()

        assert rate(126) == pytest.approx(rate(252), abs=1e-9)
        assert rate(126) == pytest.approx(0.01, abs=1e-9)

    def test_a_pair_with_too_little_overlap_is_not_measured(self) -> None:
        panel = pl.concat([_series("A", [1.0, 1.01]), _series("M", [1.0, 1.02])])
        links = pl.DataFrame({"cnpj_classe": ["A"], "cnpj_master": ["M"]})
        out = fees.measured(panel, links, business_days_per_year=252, min_overlap_days=60)
        assert out.is_empty()

    def test_a_class_whose_master_has_no_series_is_skipped_rather_than_guessed(self) -> None:
        panel = _series("A", [1.0] * 80)
        links = pl.DataFrame({"cnpj_classe": ["A"], "cnpj_master": ["M"]})
        assert fees.measured(panel, links, business_days_per_year=252).is_empty()

    def test_a_class_that_beat_its_master_reports_no_negative_fee(self) -> None:
        """A fee below zero is not a rebate, it is noise or a bad master link.
        Publishing it would hand the best possible cost percentile to a
        measurement error."""
        days = 252
        master = [1.09 ** (i / days) for i in range(days + 1)]
        feeder = [1.11 ** (i / days) for i in range(days + 1)]
        panel = pl.concat([_series("A", feeder), _series("M", master)])
        links = pl.DataFrame({"cnpj_classe": ["A"], "cnpj_master": ["M"]})
        assert fees.measured(panel, links, business_days_per_year=days).is_empty()


class TestReconcile:
    def _funds(self, declared: list[float | None]) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "cnpj_classe": [chr(65 + i) for i in range(len(declared))],
                "taxa_adm": declared,
            },
            schema={"cnpj_classe": pl.Utf8, "taxa_adm": pl.Float64},
        )

    def test_the_measured_fee_replaces_the_declared_one(self) -> None:
        out = fees.reconcile(
            self._funds([0.0004]),
            pl.DataFrame({"cnpj_classe": ["A"], "taxa_adm_medida": [0.0045]}),
        )
        assert out["taxa_adm"].to_list() == [0.0045]

    def test_what_was_declared_is_kept_so_the_delivery_can_show_both(self) -> None:
        out = fees.reconcile(
            self._funds([0.0004]),
            pl.DataFrame({"cnpj_classe": ["A"], "taxa_adm_medida": [0.0045]}),
        )
        assert out["taxa_adm_declarada"].to_list() == [0.0004]
        assert out["taxa_adm_medida"].to_list() == [0.0045]

    def test_a_measurement_below_the_filed_fee_never_flatters_the_fund(self) -> None:
        """A class cannot plausibly charge less than its manager filed for it.
        When the measured figure comes out lower, the likely causes are noise
        and the sleeve a feeder holds outside its master, not a discount. The
        higher of the two is taken, because the cost of believing a fee that is
        too low is a fund promoted to a top five it did not earn."""
        out = fees.reconcile(
            self._funds([0.0008]),
            pl.DataFrame({"cnpj_classe": ["A"], "taxa_adm_medida": [0.0001]}),
        )
        assert out["taxa_adm"].to_list() == [0.0008]
        assert out["taxa_adm_medida"].to_list() == [0.0001]

    def test_a_feeder_whose_fee_could_not_be_measured_has_no_usable_fee(self) -> None:
        """The filed field is unreliable precisely for classes that invest
        through other funds, so for those the declared value is not evidence.
        Leaving it null drops the fund through the rule that already refuses to
        rank what cannot be priced, which is the same treatment a declared zero
        gets and for the same reason."""
        funds = self._funds([0.0004]).with_columns(pl.lit("S").alias("classe_cotas"))
        out = fees.reconcile(funds, pl.DataFrame(schema={"cnpj_classe": pl.Utf8}))
        assert out["taxa_adm"].to_list() == [None]
        assert out["taxa_adm_declarada"].to_list() == [0.0004]

    def test_a_direct_fund_is_not_punished_for_a_problem_it_does_not_have(self) -> None:
        funds = self._funds([0.005]).with_columns(pl.lit("N").alias("classe_cotas"))
        out = fees.reconcile(funds, pl.DataFrame(schema={"cnpj_classe": pl.Utf8}))
        assert out["taxa_adm"].to_list() == [0.005]

    def test_a_measured_feeder_keeps_its_measured_fee(self) -> None:
        funds = self._funds([0.0004]).with_columns(pl.lit("S").alias("classe_cotas"))
        out = fees.reconcile(
            funds, pl.DataFrame({"cnpj_classe": ["A"], "taxa_adm_medida": [0.0045]})
        )
        assert out["taxa_adm"].to_list() == [0.0045]

    def test_a_fund_with_no_measurement_keeps_the_declared_fee(self) -> None:
        """The filing is wrong for one family of classes, not for the market.
        Blanking every fee we could not measure would throw away the majority
        of the universe to fix a minority."""
        out = fees.reconcile(self._funds([0.005]), pl.DataFrame(schema={"cnpj_classe": pl.Utf8}))
        assert out["taxa_adm"].to_list() == [0.005]
        assert out["taxa_adm_medida"].to_list() == [None]


class TestGateCost:
    """The fee left the score (D-051) and returns as a gate on the finalists.
    The gate reads the reliable number for each fund: the declared fee, unless
    it is the suspiciously low value the misfiling produces, where the measured
    fee replaces it. This is what keeps a genuinely cheap fund whose measurement
    ran high (Fase 1) from being struck, while still catching a fund that files
    0.040% and charges far more."""

    floor = 0.0005

    def test_a_normal_declared_fee_is_trusted_over_the_measurement(self) -> None:
        # 0.4% filed, an inflated 1.2% measured: the declared value is
        # plausible, so the measurement does not raise it. Without this, the
        # upward bias of the measurement (Fase 1) would strike a cheap fund.
        assert fees.gate_cost(0.004, 0.012, self.floor) == 0.004

    def test_a_suspiciously_low_declared_fee_is_replaced_by_the_measurement(self) -> None:
        # 0.040% filed, ~1.5% charged: the field is the misfiling of D-047.
        assert fees.gate_cost(0.0004, 0.015, self.floor) == 0.015

    def test_a_low_declared_fee_with_no_measurement_keeps_the_low_value(self) -> None:
        assert fees.gate_cost(0.0004, None, self.floor) == 0.0004

    def test_a_missing_declared_fee_falls_back_to_the_measurement(self) -> None:
        assert fees.gate_cost(None, 0.02, self.floor) == 0.02

    def test_no_number_at_all_is_none(self) -> None:
        assert fees.gate_cost(None, None, self.floor) is None
