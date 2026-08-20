"""Choosing which funds compete, and counting them at every step.

The count is the point. A pipeline that silently loses half the universe
produces valid rows, passes every schema, and ranks the wrong funds. Writing
down in advance how many should survive each filter is the only way to notice.
"""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from ranking.config import load_universe
from ranking.extract import readers
from ranking.transform import universe

REFERENCE = dt.date(2025, 12, 31)


@pytest.fixture
def filters(config_dir):
    return load_universe(config_dir / "universe.yaml").filters


# --------------------------------------------------------------------------
# Reading fees and redemption terms
# --------------------------------------------------------------------------


def test_statement_gives_fee_and_redemption(statement_path) -> None:
    frame = readers.read_statement(statement_path)
    for column in ("cnpj_classe", "data", "taxa_adm", "aplicacao_minima", "dias_resgate"):
        assert column in frame.columns


def test_redemption_days_add_conversion_and_payment(statement_path) -> None:
    """What the client experiences is the whole wait: the days until the quota
    is struck plus the days until the money lands."""
    frame = readers.read_statement(statement_path)
    row = frame.drop_nulls("dias_resgate").head(1).to_dicts()[0]
    assert row["dias_resgate"] == row["dias_conversao"] + row["dias_pagamento"]


def test_the_statement_in_force_is_the_one_on_or_before_the_date(tmp_path) -> None:
    """Point-in-time. A statement filed in March 2026 must not describe a fund
    in a ranking dated December 2025, however current it is today."""
    path = tmp_path / "extrato.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;DT_COMPTC;TAXA_ADM;QT_DIA_CONVERSAO_COTA;"
        "QT_DIA_PAGTO_RESGATE;APLIC_MIN;PUBLICO_ALVO\n"
        "00017024000153;2025-03-31;0.50;0;1;100;Público Geral\n"
        "00017024000153;2025-09-30;0.30;0;1;100;Público Geral\n"
        "00017024000153;2026-03-31;0.10;0;1;100;Público Geral\n",
        encoding="latin-1",
    )
    frame = readers.read_statement(path)
    in_force = readers.statement_in_force(frame, reference_date=REFERENCE)

    assert len(in_force) == 1
    assert in_force["taxa_adm"][0] == pytest.approx(0.003)  # 0.30% a year, as a fraction


def test_a_fund_with_no_statement_yet_is_absent(tmp_path) -> None:
    path = tmp_path / "extrato.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;DT_COMPTC;TAXA_ADM;QT_DIA_CONVERSAO_COTA;"
        "QT_DIA_PAGTO_RESGATE;APLIC_MIN;PUBLICO_ALVO\n"
        "00017024000153;2026-06-30;0.10;0;1;100;Público Geral\n",
        encoding="latin-1",
    )
    frame = readers.read_statement(path)
    assert readers.statement_in_force(frame, reference_date=REFERENCE).is_empty()


def test_percentage_fees_are_stored_as_fractions(statement_path) -> None:
    """The file says 0.20 meaning 0.20% a year. Keeping that as 0.20 would make
    a cheap fund look twenty percent expensive."""
    frame = readers.read_statement(statement_path)
    fees = frame["taxa_adm"].drop_nulls()
    assert fees.max() < 0.5, "a fixed-income admin fee above 50% a year is not a fee"


# --------------------------------------------------------------------------
# The funnel
# --------------------------------------------------------------------------


def _registry(rows: list[dict[str, object]]) -> pl.DataFrame:
    base = {
        "cnpj_classe": "00017024000153",
        "classificacao": "Renda Fixa",
        "situacao": "Em Funcionamento Normal",
        "forma_condominio": "Aberto",
        "exclusivo": "N",
        "publico_alvo": "Público Geral",
        "classificacao_anbima": "Renda Fixa Duração Baixa Soberano",
    }
    return pl.DataFrame([{**base, **row} for row in rows])


def _series(cnpjs: list[str], observations: int, net_assets: float, holders: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "cnpj_classe": [c for c in cnpjs for _ in range(observations)],
            "data": [
                REFERENCE - dt.timedelta(days=index) for _ in cnpjs for index in range(observations)
            ],
            "valor_cota": [1.0 + index / 1000 for _ in cnpjs for index in range(observations)],
            "patrimonio_liquido": [net_assets] * (len(cnpjs) * observations),
            "cotistas": [holders] * (len(cnpjs) * observations),
        }
    )


def test_each_filter_is_counted(filters) -> None:
    registry = _registry(
        [
            {"cnpj_classe": "00017024000153"},
            {"cnpj_classe": "00068305000135", "classificacao": "Ações"},
            {"cnpj_classe": "00071477000168", "situacao": "Cancelada"},
            {"cnpj_classe": "00089915000115", "forma_condominio": "Fechado"},
            {"cnpj_classe": "00180995000110", "exclusivo": "S"},
        ]
    )
    series = _series(registry["cnpj_classe"].to_list(), 250, 50e6, 500)
    terms = pl.DataFrame(
        {
            "cnpj_classe": registry["cnpj_classe"].to_list(),
            "taxa_adm": [0.002] * 5,
            "dias_resgate": [1] * 5,
            "aplicacao_minima": [100.0] * 5,
        }
    )

    result = universe.build(registry, series, terms, filters=filters, reference_date=REFERENCE)

    assert result.counts["registered_classes"] == 5
    assert result.counts["fixed_income"] == 4
    assert result.counts["operating"] == 3
    assert result.counts["open_ended"] == 2
    assert result.counts["non_exclusive"] == 1
    assert len(result.funds) == 1


def test_counts_never_increase(filters) -> None:
    registry = _registry([{"cnpj_classe": f"{index:014d}"} for index in range(1, 6)])
    series = _series(registry["cnpj_classe"].to_list(), 250, 50e6, 500)
    terms = pl.DataFrame(
        {
            "cnpj_classe": registry["cnpj_classe"].to_list(),
            "taxa_adm": [0.002] * 5,
            "dias_resgate": [1] * 5,
            "aplicacao_minima": [100.0] * 5,
        }
    )
    counts = list(
        universe.build(
            registry, series, terms, filters=filters, reference_date=REFERENCE
        ).counts.values()
    )
    assert counts == sorted(counts, reverse=True)


def test_a_thin_series_is_excluded(filters) -> None:
    registry = _registry([{"cnpj_classe": "00017024000153"}])
    series = _series(["00017024000153"], 10, 50e6, 500)  # far below min_observations
    terms = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "taxa_adm": [0.002],
            "dias_resgate": [1],
            "aplicacao_minima": [100.0],
        }
    )
    result = universe.build(registry, series, terms, filters=filters, reference_date=REFERENCE)
    assert result.funds.is_empty()


def test_a_fund_without_published_terms_is_excluded(filters) -> None:
    """Decision D-013: no recommendation without a price tag."""
    registry = _registry([{"cnpj_classe": "00017024000153"}])
    series = _series(["00017024000153"], 250, 50e6, 500)
    empty_terms = pl.DataFrame(
        schema={
            "cnpj_classe": pl.String,
            "taxa_adm": pl.Float64,
            "dias_resgate": pl.Int64,
            "aplicacao_minima": pl.Float64,
        }
    )
    result = universe.build(
        registry, series, empty_terms, filters=filters, reference_date=REFERENCE
    )
    assert result.funds.is_empty()
    assert result.counts["with_fee_and_redemption"] == 0


def test_the_join_never_multiplies_funds(filters) -> None:
    """One row per fund at the end, whatever the inputs did."""
    registry = _registry([{"cnpj_classe": f"{index:014d}"} for index in range(1, 4)])
    series = _series(registry["cnpj_classe"].to_list(), 250, 50e6, 500)
    terms = pl.DataFrame(
        {
            "cnpj_classe": registry["cnpj_classe"].to_list() * 2,  # duplicated on purpose
            "taxa_adm": [0.002] * 6,
            "dias_resgate": [1] * 6,
            "aplicacao_minima": [100.0] * 6,
        }
    )
    result = universe.build(registry, series, terms, filters=filters, reference_date=REFERENCE)
    assert len(result.funds) == result.funds["cnpj_classe"].n_unique()


def test_business_day_terms_are_converted_to_calendar_days(tmp_path) -> None:
    """A fund quoting "5 business days" makes the client wait a week. Treating
    that as five would flatter it against a fund quoting five calendar days,
    and redemption speed is the second-heaviest weight for retail."""
    path = tmp_path / "extrato.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;DT_COMPTC;TAXA_ADM;QT_DIA_CONVERSAO_COTA;QT_DIA_PAGTO_RESGATE;"
        "TP_DIA_PAGTO_RESGATE;APLIC_MIN\n"
        "00017024000153;2025-12-01;0.50;0;5;DIAS ÚTEIS;100\n"
        "00068305000135;2025-12-01;0.50;0;5;DIAS CORRIDOS;100\n",
        encoding="latin-1",
    )
    frame = readers.read_statement(path).sort("cnpj_classe")
    assert frame["dias_resgate"].to_list() == [7, 5]


def test_same_day_redemption_is_zero_in_either_unit(tmp_path) -> None:
    path = tmp_path / "extrato.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;DT_COMPTC;TAXA_ADM;QT_DIA_CONVERSAO_COTA;QT_DIA_PAGTO_RESGATE;"
        "TP_DIA_PAGTO_RESGATE;APLIC_MIN\n"
        "00017024000153;2025-12-01;0.50;0;0;DIAS ÚTEIS;100\n",
        encoding="latin-1",
    )
    assert readers.read_statement(path)["dias_resgate"][0] == 0


# --------------------------------------------------------------------------
# The factsheet — the other half of the fee coverage
#
# The statement alone reaches about 70% of the funds we can rank. The factsheet
# is mandatory precisely for retail funds, which are the main deliverable, so
# leaving it out would cripple the profile that matters most.
# --------------------------------------------------------------------------


def test_factsheet_gives_the_same_shape_as_the_statement(tmp_path) -> None:
    """Both sources must arrive in one vocabulary, or the merge is guesswork."""
    path = tmp_path / "lamina.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DT_COMPTC;TAXA_ADM;QT_DIA_CONVERSAO_COTA_RESGATE;"
        "QT_DIA_PAGTO_RESGATE;TP_DIA_PAGTO_RESGATE;INVEST_INICIAL_MIN\n"
        "00017024000153;;2025-12-01;0.50;0;1;DIAS CORRIDOS;100\n",
        encoding="latin-1",
    )
    frame = readers.read_factsheet(path)
    for column in ("cnpj_classe", "data", "taxa_adm", "dias_resgate", "aplicacao_minima"):
        assert column in frame.columns
    assert frame["taxa_adm"][0] == pytest.approx(0.005)


def test_factsheet_subclass_rows_are_excluded(tmp_path) -> None:
    """Same trap as the daily report: subclass rows repeat the class."""
    path = tmp_path / "lamina.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DT_COMPTC;TAXA_ADM;QT_DIA_CONVERSAO_COTA_RESGATE;"
        "QT_DIA_PAGTO_RESGATE;TP_DIA_PAGTO_RESGATE;INVEST_INICIAL_MIN\n"
        "00017024000153;;2025-12-01;0.50;0;1;DIAS CORRIDOS;100\n"
        "00017024000153;SUB1;2025-12-01;9.00;0;1;DIAS CORRIDOS;100\n",
        encoding="latin-1",
    )
    frame = readers.read_factsheet(path)
    assert len(frame) == 1
    assert frame["taxa_adm"][0] == pytest.approx(0.005)


def test_the_statement_wins_when_both_sources_have_a_fund() -> None:
    """One fund, one set of terms. The statement is the more formal filing."""
    statement = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "taxa_adm": [0.002],
            "dias_resgate": [1],
            "aplicacao_minima": [100.0],
        }
    )
    factsheet = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "taxa_adm": [0.009],
            "dias_resgate": [30],
            "aplicacao_minima": [500.0],
        }
    )
    merged = readers.combine_terms(statement, factsheet)
    assert len(merged) == 1
    assert merged["taxa_adm"][0] == pytest.approx(0.002)
    assert merged["fonte_taxa"][0] == "EXTRATO"


def test_the_factsheet_fills_the_gaps() -> None:
    statement = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "taxa_adm": [0.002],
            "dias_resgate": [1],
            "aplicacao_minima": [100.0],
        }
    )
    factsheet = pl.DataFrame(
        {
            "cnpj_classe": ["00068305000135"],
            "taxa_adm": [0.009],
            "dias_resgate": [30],
            "aplicacao_minima": [500.0],
        }
    )
    merged = readers.combine_terms(statement, factsheet).sort("cnpj_classe")
    assert len(merged) == 2
    assert merged["fonte_taxa"].to_list() == ["EXTRATO", "LAMINA"]


def test_the_source_of_every_fee_is_recorded() -> None:
    """The output promises a `fee_source` per fund. Whoever reads the ranking
    is entitled to know where the number they are being charged came from."""
    statement = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "taxa_adm": [0.002],
            "dias_resgate": [1],
            "aplicacao_minima": [100.0],
        }
    )
    empty = pl.DataFrame(
        schema={
            "cnpj_classe": pl.String,
            "taxa_adm": pl.Float64,
            "dias_resgate": pl.Int64,
            "aplicacao_minima": pl.Float64,
        }
    )
    merged = readers.combine_terms(statement, empty)
    assert set(merged["fonte_taxa"].to_list()) <= {"EXTRATO", "LAMINA"}


def test_combining_never_multiplies_a_fund() -> None:
    statement = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"] * 2,
            "taxa_adm": [0.002, 0.003],
            "dias_resgate": [1, 1],
            "aplicacao_minima": [100.0, 100.0],
        }
    )
    factsheet = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "taxa_adm": [0.009],
            "dias_resgate": [30],
            "aplicacao_minima": [500.0],
        }
    )
    merged = readers.combine_terms(statement, factsheet)
    assert len(merged) == 1


# --------------------------------------------------------------------------
# A declared fee of zero is not a free fund
# --------------------------------------------------------------------------


def test_a_declared_zero_fee_is_treated_as_unknown() -> None:
    """Roughly a fifth of funds with fewer than a hundred shareholders declare
    an admin fee of exactly zero, against six per cent everywhere else. The fee
    is charged at the feeder or the distributor, not waived — and cost is the
    heaviest weight in both profiles, so letting a zero take the top percentile
    hands the best score to whoever disclosed least.
    """
    frame = pl.DataFrame({"cnpj_classe": ["a", "b", "c"], "taxa_adm": [0.0, 0.002, None]})
    cleaned = universe.blank_undisclosed_fees(frame)
    assert cleaned["taxa_adm"].to_list() == [None, 0.002, None]


def test_the_declared_value_is_kept_for_reporting() -> None:
    """We stop scoring on it; we do not pretend it was never filed."""
    frame = pl.DataFrame({"cnpj_classe": ["a"], "taxa_adm": [0.0]})
    cleaned = universe.blank_undisclosed_fees(frame)
    assert cleaned["taxa_adm_declarada"][0] == 0.0
    assert cleaned["taxa_zero_declarada"][0] is True


def test_an_ordinary_fee_is_left_alone() -> None:
    frame = pl.DataFrame({"cnpj_classe": ["a"], "taxa_adm": [0.005]})
    cleaned = universe.blank_undisclosed_fees(frame)
    assert cleaned["taxa_adm"][0] == pytest.approx(0.005)
    assert cleaned["taxa_zero_declarada"][0] is False
