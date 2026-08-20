"""Turning what the CVM publishes into something joinable.

Two jobs, both of which look trivial and are not:

- CNPJ arrives formatted in one file and unformatted in another, so any join
  written against the raw values silently matches nothing.
- The registry's `Data_Inicio` is not the fund's start date. It is the date the
  fund adapted to CVM resolution 175, which for most funds is 2024 or 2025.
  Reading age from it would call a thirty-year-old fund a newborn.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from typing import Any

_FIRST_WEIGHTS = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_SECOND_WEIGHTS = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)

DAYS_IN_YEAR = 365.25


def digits_only(raw: str | None) -> str:
    """Strip formatting without judging the result.

    Used while reading files, where an unusable CNPJ must survive long enough
    to be quarantined with a reason rather than blow up the whole read.
    """
    return "".join(character for character in (raw or "") if character.isdigit())


def is_valid_cnpj(candidate: str) -> bool:
    """Check the two verification digits.

    Verified against every CNPJ in the CVM registry and in the December 2025
    daily report — 62,058 values, none rejected — so this is safe to apply
    strictly. A validation that quietly discards real funds would be worse
    than no validation at all.
    """
    if len(candidate) != 14 or not candidate.isdigit():
        return False
    if candidate == candidate[0] * 14:
        return False
    for size, weights in ((12, _FIRST_WEIGHTS), (13, _SECOND_WEIGHTS)):
        remainder = sum(int(candidate[i]) * weights[i] for i in range(size)) % 11
        expected = 0 if remainder < 2 else 11 - remainder
        if int(candidate[size]) != expected:
            return False
    return True


def cnpj(raw: str | None) -> str:
    """Normalise to fourteen digits, refusing anything that is not a CNPJ."""
    candidate = digits_only(raw)
    if len(candidate) != 14:
        raise ValueError(f"CNPJ must have 14 digits, got {len(candidate)}: {raw!r}")
    if not is_valid_cnpj(candidate):
        raise ValueError(f"CNPJ check digits do not match: {raw!r}")
    return candidate


def fund_age_years(row: Mapping[str, Any], as_of: dt.date) -> float:
    """Age in years, from the fund's constitution — never from the registry's
    `Data_Inicio`, which is the resolution-175 adaptation date.

    Falls back to the first observed quota date when the constitution date is
    missing, because an observed series is still evidence of existence.
    """
    started = row.get("data_constituicao") or row.get("primeira_cota")
    if started is None:
        raise ValueError(
            "cannot determine fund age: no constitution date and no observed quota. "
            "Note that data_adaptacao_rcvm175 is NOT a valid substitute."
        )
    if isinstance(started, dt.datetime):
        started = started.date()
    if not isinstance(started, dt.date):
        started = dt.date.fromisoformat(str(started)[:10])
    return (as_of - started).days / DAYS_IN_YEAR
