"""Reading and joining the CVM registry files.

The tests about row counts are not pedantry. The CVM registry ships duplicate
rows — 1,046 fund ids appear more than once in `registro_fundo.csv`, with
identical content — and a plain left join therefore multiplies classes. The
resulting universe is a few percent too large, every count downstream is
wrong, and nothing raises. The funnel check does not catch it either, because
the inflation sits inside the tolerance.
"""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from ranking.extract import readers


@pytest.fixture
def duplicated_registry(tmp_path):
    """A class registry and a fund registry where one fund appears four times,
    exactly as the real file does."""
    class_csv = tmp_path / "registro_classe.csv"
    class_csv.write_text(
        "ID_Registro_Fundo;ID_Registro_Classe;CNPJ_Classe;Denominacao_Social;Situacao;"
        "Data_Inicio;Classificacao;Classificacao_Anbima;Forma_Condominio;Exclusivo;Publico_Alvo\n"
        "56975;1;00068305000135;FUNDO A;Em Funcionamento Normal;2025-05-12;Renda Fixa;"
        "Renda Fixa Duração Baixa Soberano;Aberto;N;Público Geral\n",
        encoding="latin-1",
    )
    fund_csv = tmp_path / "registro_fundo.csv"
    row = "56975;29091970000121;FUNDO A;2018-02-20;Em Funcionamento Normal;ADMIN;GESTOR\n"
    fund_csv.write_text(
        "ID_Registro_Fundo;CNPJ_Fundo;Denominacao_Social;Data_Constituicao;Situacao;"
        "Administrador;Gestor\n" + row * 4,
        encoding="latin-1",
    )
    return class_csv, fund_csv


def test_duplicate_fund_rows_do_not_multiply_classes(duplicated_registry) -> None:
    """One class joined against four identical fund rows is still one class."""
    class_csv, fund_csv = duplicated_registry
    joined = readers.read_registry(class_csv, fund_csv)
    assert len(joined) == 1


def test_the_join_never_grows_the_class_table(duplicated_registry) -> None:
    class_csv, fund_csv = duplicated_registry
    classes = readers.read_registry_classes(class_csv)
    joined = readers.read_registry(class_csv, fund_csv)
    assert len(joined) <= len(classes)


def test_class_ids_are_unique_after_reading(duplicated_registry) -> None:
    class_csv, _ = duplicated_registry
    classes = readers.read_registry_classes(class_csv)
    assert classes["id_registro_classe"].n_unique() == len(classes)


def test_fund_ids_are_unique_after_reading(duplicated_registry) -> None:
    _, fund_csv = duplicated_registry
    funds = readers.read_registry_funds(fund_csv)
    assert funds["id_registro_fundo"].n_unique() == len(funds)


def test_the_constitution_date_survives_deduplication(duplicated_registry) -> None:
    """Deduplicating must not cost us the one field the join exists for."""
    class_csv, fund_csv = duplicated_registry
    joined = readers.read_registry(class_csv, fund_csv)
    assert joined["data_constituicao"][0] == dt.date(2018, 2, 20)


def test_real_fixture_registry_does_not_inflate(registry_class_path, registry_fund_path) -> None:
    classes = readers.read_registry_classes(registry_class_path)
    joined = readers.read_registry(registry_class_path, registry_fund_path)
    assert len(joined) == len(classes)


# --------------------------------------------------------------------------
# Reading the daily report
# --------------------------------------------------------------------------


def test_daily_report_types_are_cast_not_guessed(daily_report_path) -> None:
    frame = readers.read_daily_report(daily_report_path)
    assert frame.schema["data"] == pl.Date
    assert frame.schema["valor_cota"] == pl.Float64
    assert frame.schema["cotistas"] == pl.Int64


def test_unparseable_numbers_become_null_rather_than_crashing(dirty_daily_report_path) -> None:
    """A bad value must survive as a null so the contract layer can quarantine
    the row with a reason, instead of the read blowing up on line one."""
    frame = readers.read_daily_report(dirty_daily_report_path)
    assert frame["valor_cota"].is_null().any()


def test_cnpj_is_stripped_but_not_judged_at_read_time(dirty_daily_report_path) -> None:
    frame = readers.read_daily_report(dirty_daily_report_path)
    assert "123" in frame["cnpj_classe"].to_list()
    assert not any("." in value for value in frame["cnpj_classe"].to_list())


# --------------------------------------------------------------------------
# The CVM uses the double quote as an ordinary character
# --------------------------------------------------------------------------


def test_a_stray_double_quote_does_not_swallow_the_next_rows(tmp_path) -> None:
    """`extrato_fi_2025.csv` contains 194 loose double quotes in free-text
    fields — investment policy prose, mostly. A reader that treats them as
    field delimiters starts a quoted region, eats every following newline
    until the next quote, and fails with "CSV malformed" halfway through a
    12 MB file. The CVM never quotes fields: every line has exactly the same
    number of semicolons whether quotes are present or not.
    """
    path = tmp_path / "extrato.csv"
    path.write_text(
        "CNPJ_FUNDO_CLASSE;DT_COMPTC;POLIT_INVEST\n"
        '00017024000153;2025-12-01;aplica em titulos de 5" de duracao\n'
        "00068305000135;2025-12-02;politica normal\n"
        "00071477000168;2025-12-03;outra politica\n",
        encoding="latin-1",
    )
    frame = readers.read_latin1_csv(path)
    assert len(frame) == 3
    assert frame["CNPJ_FUNDO_CLASSE"].to_list()[-1] == "00071477000168"


def test_an_odd_number_of_quotes_still_parses(tmp_path) -> None:
    path = tmp_path / "extrato.csv"
    path.write_text(
        'A;B\n1;abertura " sem fechamento\n2;normal\n',
        encoding="latin-1",
    )
    assert len(readers.read_latin1_csv(path)) == 2
