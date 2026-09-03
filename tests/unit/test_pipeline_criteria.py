"""The two peer criteria added to line up with how Decade evaluates a fund:
how long it has run, and whether its vehicle escapes the come-cotas that a
direct instrument avoids. See decision D-054.
"""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from ranking import pipeline


def test_tax_efficiency_rewards_the_exempt_infra_fund() -> None:
    frame = pl.DataFrame(
        {
            "denominacao_social": [
                "FUNDO INCENTIVADO DE INFRA",
                "FUNDO RF LONGO PRAZO",
                "FUNDO RF CURTO PRAZO",
            ],
            "classificacao_anbima": [
                "Renda Fixa Duração Alta",
                "Renda Fixa Duração Baixa",
                "Renda Fixa Simples",
            ],
            "tributacao_longo_prazo": ["S", "S", "N"],
        }
    )
    out = frame.with_columns(pipeline._tax_efficiency_expr().alias("te"))
    # Exempt (no come-cotas) beats a long-term regressive fund, which beats a
    # short-term one.
    assert out["te"].to_list() == [1.0, 0.5, 0.0]


def test_tax_efficiency_detects_infra_in_the_category_name() -> None:
    frame = pl.DataFrame(
        {
            "denominacao_social": ["FUNDO RF QUALQUER"],
            "classificacao_anbima": ["Renda Fixa Duração Alta Infraestrutura"],
            "tributacao_longo_prazo": ["N"],
        }
    )
    out = frame.with_columns(pipeline._tax_efficiency_expr().alias("te"))
    assert out["te"].to_list() == [1.0]


def test_track_record_uses_the_constitution_date_not_the_first_quota() -> None:
    frame = pl.DataFrame(
        {
            "data_constituicao": [dt.date(1994, 5, 26), None],
            "primeira_data": [dt.date(2020, 1, 1), dt.date(2023, 1, 1)],
        },
        schema_overrides={"data_constituicao": pl.Date, "primeira_data": pl.Date},
    )
    out = frame.with_columns(pipeline._track_record_expr(dt.date(2024, 5, 26)).alias("tr"))
    values = out["tr"].to_list()
    # The 1994 fund is thirty, from its constitution, not four from its first
    # observed quota in 2020 (trap 3).
    assert values[0] == pytest.approx(30.0, abs=0.1)
    # With no constitution date, the age falls back to the first quota.
    assert values[1] == pytest.approx(1.4, abs=0.2)
