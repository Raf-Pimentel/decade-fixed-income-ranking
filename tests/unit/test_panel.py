"""Turning a year of daily quotas into one row of numbers per fund.

This is where the arithmetic in `metrics` meets the real shape of the data:
funds that start mid-period, series with gaps, a benchmark published on a
different set of days. Getting any of that wrong produces numbers that look
entirely plausible.
"""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from ranking.extract import readers
from ranking.transform import panel

REFERENCE = dt.date(2025, 12, 31)


# --------------------------------------------------------------------------
# Reading the benchmark
# --------------------------------------------------------------------------


def test_cdi_is_read_as_a_daily_fraction(cdi_path) -> None:
    """The Central Bank publishes percent per day. Carrying 0.055 through as a
    5.5% daily rate would compound to something absurd over a year."""
    frame = readers.read_cdi(cdi_path)
    assert set(frame.columns) >= {"data", "taxa"}
    assert frame["taxa"].max() < 0.01, "a daily CDI above 1% is a unit error"
    assert frame["taxa"].min() > 0


def test_cdi_dates_are_parsed_day_first(cdi_path) -> None:
    """The Central Bank writes 05/12/2025 meaning 5 December."""
    frame = readers.read_cdi(cdi_path)
    assert frame["data"].min() >= dt.date(2025, 10, 1)
    assert frame["data"].max() <= dt.date(2025, 12, 31)


def test_the_benchmark_is_cut_at_the_reference_date(cdi_path) -> None:
    frame = readers.read_cdi(cdi_path)
    windowed = panel.benchmark_window(frame, start=dt.date(2025, 11, 1), end=dt.date(2025, 11, 30))
    assert windowed["data"].min() >= dt.date(2025, 11, 1)
    assert windowed["data"].max() <= dt.date(2025, 11, 30)


# --------------------------------------------------------------------------
# Building the panel
# --------------------------------------------------------------------------


def _two_funds() -> pl.DataFrame:
    days = [dt.date(2025, 12, 1) + dt.timedelta(days=i) for i in range(10)]
    rows = []
    for cnpj, step in (("00017024000153", 0.001), ("00068305000135", 0.002)):
        quota = 100.0
        for day in days:
            rows.append(
                {
                    "cnpj_classe": cnpj,
                    "data": day,
                    "valor_cota": quota,
                    "patrimonio_liquido": 100e6,
                    "cotistas": 1_000,
                    "captacao": 10.0,
                    "resgate": 5.0,
                }
            )
            quota *= 1 + step
    return pl.DataFrame(rows)


def test_one_row_per_fund(cdi_path) -> None:
    built = panel.build(_two_funds(), benchmark_rate=0.01, reference_date=REFERENCE)
    assert len(built) == 2
    assert built["cnpj_classe"].n_unique() == 2


def test_every_declared_metric_is_present(cdi_path) -> None:
    built = panel.build(_two_funds(), benchmark_rate=0.01, reference_date=REFERENCE)
    for column in (
        "retorno",
        "excesso",
        "volatilidade",
        "retorno_por_risco",
        "pior_queda",
        "dias_negativos",
        "estabilidade_fluxo",
        "observacoes",
    ):
        assert column in built.columns, column


def test_the_faster_fund_shows_the_higher_return() -> None:
    built = panel.build(_two_funds(), benchmark_rate=0.01, reference_date=REFERENCE).sort(
        "cnpj_classe"
    )
    assert built["retorno"][1] > built["retorno"][0]


def test_returns_agree_with_the_metric_functions() -> None:
    """The panel must not re-derive the arithmetic; it must call it."""
    from ranking.transform import metrics

    frame = _two_funds()
    built = panel.build(frame, benchmark_rate=0.01, reference_date=REFERENCE)
    for row in built.iter_rows(named=True):
        quotas = (
            frame.filter(pl.col("cnpj_classe") == row["cnpj_classe"])
            .sort("data")["valor_cota"]
            .to_list()
        )
        assert row["retorno"] == pytest.approx(metrics.cumulative_return(quotas))


def test_a_fund_whose_quota_never_moves_is_dropped_not_ranked() -> None:
    """Zero volatility would make return-per-risk infinite. The fund has
    stopped being priced; it must not win by standing still."""
    days = [dt.date(2025, 12, 1) + dt.timedelta(days=i) for i in range(10)]
    frozen = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"] * 10,
            "data": days,
            "valor_cota": [100.0] * 10,
            "patrimonio_liquido": [100e6] * 10,
            "cotistas": [1_000] * 10,
            "captacao": [0.0] * 10,
            "resgate": [0.0] * 10,
        }
    )
    built = panel.build(frozen, benchmark_rate=0.01, reference_date=REFERENCE)
    assert built.is_empty() or built["retorno_por_risco"].is_null().all()


def test_no_observation_after_the_reference_date_is_used() -> None:
    """Point-in-time, enforced again at the last moment before the numbers are
    computed. A single leaked day would silently invalidate the backtest."""
    frame = _two_funds()
    built = panel.build(frame, benchmark_rate=0.01, reference_date=dt.date(2025, 12, 5))
    assert built["observacoes"].max() == 5


def test_a_fund_with_one_observation_is_excluded() -> None:
    single = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "data": [dt.date(2025, 12, 1)],
            "valor_cota": [100.0],
            "patrimonio_liquido": [100e6],
            "cotistas": [1_000],
            "captacao": [0.0],
            "resgate": [0.0],
        }
    )
    assert panel.build(single, benchmark_rate=0.01, reference_date=REFERENCE).is_empty()


def test_excess_is_measured_against_the_benchmark_not_zero() -> None:
    built = panel.build(_two_funds(), benchmark_rate=0.05, reference_date=REFERENCE).sort(
        "cnpj_classe"
    )
    assert built["excesso"][0] == pytest.approx(built["retorno"][0] - 0.05)


def test_building_twice_gives_the_same_numbers() -> None:
    frame = _two_funds()
    first = panel.build(frame, benchmark_rate=0.01, reference_date=REFERENCE)
    second = panel.build(frame, benchmark_rate=0.01, reference_date=REFERENCE)
    assert first.equals(second)
