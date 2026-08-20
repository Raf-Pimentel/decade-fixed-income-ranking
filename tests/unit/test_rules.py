"""Business rules that the schema cannot express."""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from ranking.contracts import rules


def _series(quotas: list[float], cnpj: str = "00017024000153") -> pl.DataFrame:
    start = dt.date(2025, 10, 1)
    return pl.DataFrame(
        {
            "cnpj_classe": [cnpj] * len(quotas),
            "data": [start + dt.timedelta(days=i) for i in range(len(quotas))],
            "valor_cota": quotas,
        }
    )


# --------------------------------------------------------------------------
# Implausible moves are flagged, never dropped
# --------------------------------------------------------------------------


def test_a_calm_series_flags_nothing() -> None:
    frame = rules.flag_implausible_moves(_series([100.0, 100.5, 101.0, 101.4]))
    assert not frame["implausible_move"].any()


def test_a_fifty_percent_fall_is_flagged() -> None:
    frame = rules.flag_implausible_moves(_series([100.0, 50.0, 50.2]))
    assert frame["implausible_move"].to_list() == [False, True, False]


def test_the_first_observation_is_never_flagged() -> None:
    """There is no previous day to compare against."""
    frame = rules.flag_implausible_moves(_series([100.0, 100.1]))
    assert frame["implausible_move"][0] is False


def test_flagging_removes_no_rows() -> None:
    original = _series([100.0, 50.0, 25.0, 12.0])
    assert len(rules.flag_implausible_moves(original)) == len(original)


def test_funds_do_not_contaminate_each_other() -> None:
    """The move must be measured within a fund, not across the file."""
    frame = pl.concat([_series([100.0, 100.1]), _series([1.0, 1.001], cnpj="00068305000135")])
    flagged = rules.flag_implausible_moves(frame)
    assert not flagged["implausible_move"].any()


# --------------------------------------------------------------------------
# Stale quotas
# --------------------------------------------------------------------------


def test_a_quota_frozen_for_weeks_is_flagged() -> None:
    """Not a calm fund — a fund that stopped being priced. Its volatility
    would read as near zero and its score would be spectacular."""
    frame = rules.flag_stale_quotas(_series([100.0] * 15), max_days=10)
    assert frame["stale_quota"].any()


def test_a_moving_quota_is_never_stale() -> None:
    frame = rules.flag_stale_quotas(_series([100.0 + i for i in range(30)]), max_days=10)
    assert not frame["stale_quota"].any()


def test_unchanged_days_scattered_across_the_series_do_not_add_up() -> None:
    """The rule is about a *run* of frozen days. Twelve unchanged days spread
    over a year is an ordinary fund; twelve in a row is a dead one."""
    quotas: list[float] = []
    value = 100.0
    for _ in range(20):
        quotas += [value, value]  # one unchanged day, then move on
        value += 0.1
    frame = rules.flag_stale_quotas(_series(quotas), max_days=10)
    assert not frame["stale_quota"].any(), "scattered flat days must not accumulate"


def test_the_run_must_reach_the_threshold() -> None:
    nine_flat = _series([100.0] * 10 + [101.0])  # nine unchanged days after the first
    assert not rules.flag_stale_quotas(nine_flat, max_days=10)["stale_quota"].any()

    ten_flat = _series([100.0] * 11 + [101.0])
    assert rules.flag_stale_quotas(ten_flat, max_days=10)["stale_quota"].any()


@pytest.mark.parametrize("max_days", [1, 5, 30])
def test_threshold_is_configurable(max_days: int) -> None:
    frame = rules.flag_stale_quotas(_series([100.0] * 40), max_days=max_days)
    assert frame["stale_quota"].any()
