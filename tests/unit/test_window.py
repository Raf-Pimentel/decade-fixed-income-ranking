"""The measurement window is exactly as long as it says it is.

A window that is one month longer than its label does not raise anything, does
not fail a schema and does not look wrong in a table. It publishes a thirteen
month return under the words "twelve months", and compares it against a
benchmark compounded over thirteen months — internally consistent, externally
impossible to reconcile against anything the fund itself publishes.

These are the tests for the arithmetic and for its consequence in the delivered
file, which are different failures: the first is a function returning the wrong
date, the second is a report describing the right window with the wrong words.
"""

from __future__ import annotations

import datetime as dt

import pytest

from ranking.pipeline import _months_between, _window_start

BUSINESS_DAYS_IN_A_YEAR = 252


@pytest.mark.parametrize(
    ("reference", "months", "expected"),
    [
        (dt.date(2025, 12, 31), 12, dt.date(2025, 1, 1)),
        (dt.date(2025, 12, 31), 24, dt.date(2024, 1, 1)),
        (dt.date(2025, 12, 31), 6, dt.date(2025, 7, 1)),
        (dt.date(2025, 12, 31), 3, dt.date(2025, 10, 1)),
        (dt.date(2025, 3, 31), 12, dt.date(2024, 4, 1)),
        (dt.date(2025, 6, 30), 12, dt.date(2024, 7, 1)),
        (dt.date(2025, 9, 30), 12, dt.date(2024, 10, 1)),
    ],
)
def test_the_window_starts_the_day_after_the_same_date_months_back(
    reference: dt.date, months: int, expected: dt.date
) -> None:
    assert _window_start(reference, months) == expected


@pytest.mark.parametrize("months", [1, 3, 6, 12, 24, 36])
def test_the_window_spans_exactly_the_months_it_claims(months: int) -> None:
    """The property, rather than a table of cases: whatever the reference date,
    a window of N months touches N calendar months."""
    reference = dt.date(2025, 12, 31)
    assert len(_months_between(_window_start(reference, months), reference)) == months


def test_a_short_month_does_not_push_the_window_into_the_next_one() -> None:
    """31 March minus one month has no 31 February to land on. Clamping to the
    last day of the shorter month and stepping forward gives the first of
    March, which is the answer a person would give."""
    assert _window_start(dt.date(2025, 3, 31), 1) == dt.date(2025, 3, 1)


def test_a_leap_day_reference_resolves() -> None:
    """29 February exists in 2024 and not in 2023, so counting twelve months
    back has to land on the 28th and then step forward."""
    assert _window_start(dt.date(2024, 2, 29), 12) == dt.date(2023, 3, 1)


def test_a_twelve_month_window_holds_about_a_year_of_business_days() -> None:
    """The check that connects the calendar to the data. A twelve-month window
    should hold roughly 252 business days; thirteen months would hold about
    273, and that gap is what makes a mislabelled window visible."""
    start = _window_start(dt.date(2025, 12, 31), 12)
    weekdays = sum(
        1
        for offset in range((dt.date(2025, 12, 31) - start).days + 1)
        if (start + dt.timedelta(days=offset)).weekday() < 5
    )
    assert BUSINESS_DAYS_IN_A_YEAR <= weekdays <= BUSINESS_DAYS_IN_A_YEAR + 10
