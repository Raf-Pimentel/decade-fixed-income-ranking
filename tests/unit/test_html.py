"""The visual page, regenerated on every run.

It exists so that the current ranking can be looked at rather than read, which
matters for a walkthrough. Everything it shows comes from the same payload the
JSON is built from — a page that could drift from `ranking.json` would be a
second source of truth, and this project has enough of those already.
"""

from __future__ import annotations

import datetime as dt

import pytest

from ranking.contracts.schemas import ProfileRanking, RankedFund, RankingOutput
from ranking.publish import html


@pytest.fixture
def payload() -> RankingOutput:
    fund = RankedFund(
        rank=1,
        cnpj_classe="00017024000153",
        name="ITAÚ CRÉDITO BANCÁRIO RENDA FIXA",
        manager="ITAU UNIBANCO ASSET",
        peer_group="Renda Fixa Duração Baixa Soberano",
        score=82.6,
        appearance_rate=1.0,
        metrics={
            "retorno": 0.1542,
            "excesso": 0.0003,
            "taxa_adm": 0.0004,
            "dias_resgate": 0,
            "pior_queda": -0.0002,
            "patrimonio_medio": 19_200_000_000.0,
            "cotistas": 141_715,
        },
        percentiles={"admin_fee": 0.9},
        rationale="Taxa baixa, resgate no mesmo dia.",
    )
    return RankingOutput(
        schema_version="1.0.0",
        reference_date=dt.date(2025, 12, 31),
        lookback_months=12,
        sources={"inf_diario_fi_202512.zip": "abc123"},
        profiles=[
            ProfileRanking(
                profile_id="varejo_liquidez",
                label="Reserva de emergência",
                eligible_universe_size=218,
                weights={"admin_fee": 30, "volatility": 20},
                top=[fund],
            )
        ],
    )


def test_the_page_is_written(payload, tmp_path) -> None:
    target = tmp_path / "ranking.html"
    html.write_html(payload, target)
    assert target.exists()


def test_it_shows_the_funds_and_the_profile(payload, tmp_path) -> None:
    target = tmp_path / "ranking.html"
    html.write_html(payload, target)
    page = target.read_text(encoding="utf-8")
    assert "ITAÚ CRÉDITO BANCÁRIO RENDA FIXA" in page
    assert "Reserva de emergência" in page
    assert "218" in page


def test_it_states_the_reference_date(payload, tmp_path) -> None:
    target = tmp_path / "ranking.html"
    html.write_html(payload, target)
    assert "31/12/2025" in target.read_text(encoding="utf-8")


def test_it_is_self_contained(payload, tmp_path) -> None:
    """No external stylesheet, no font host, no script from a CDN. The page has
    to open from a file:// URL on a laptop with no network — which is exactly
    the situation of someone recording a walkthrough."""
    target = tmp_path / "ranking.html"
    html.write_html(payload, target)
    page = target.read_text(encoding="utf-8")
    assert "http://" not in page
    assert "https://" not in page


def test_fund_names_are_escaped(tmp_path) -> None:
    """Fund names come from a CVM file, and the CVM does not promise they are
    free of angle brackets. An unescaped name would silently break the page."""
    fund = RankedFund(
        rank=1,
        cnpj_classe="00017024000153",
        name="FUNDO <script>alert(1)</script> & CIA",
        manager=None,
        score=1.0,
        appearance_rate=0.5,
        rationale="x",
    )
    payload = RankingOutput(
        schema_version="1.0.0",
        reference_date=dt.date(2025, 12, 31),
        lookback_months=12,
        sources={},
        profiles=[
            ProfileRanking(
                profile_id="p",
                label="P",
                eligible_universe_size=1,
                weights={"admin_fee": 100},
                top=[fund],
            )
        ],
    )
    target = tmp_path / "ranking.html"
    html.write_html(payload, target)
    page = target.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
    assert "&amp; CIA" in page


def test_the_validation_verdict_appears_when_given(payload, tmp_path) -> None:
    target = tmp_path / "ranking.html"
    html.write_html(payload, target, validation="Método validado: 3 de 3.")
    assert "Método validado: 3 de 3." in target.read_text(encoding="utf-8")


def test_the_page_says_what_the_method_cannot_see(payload, tmp_path) -> None:
    """The limitations travel with the numbers. A page showing only the winners
    is the thing this project has spent its whole life avoiding."""
    target = tmp_path / "ranking.html"
    html.write_html(payload, target)
    page = target.read_text(encoding="utf-8").lower()
    assert "carteira" in page
    assert "2026" in page
