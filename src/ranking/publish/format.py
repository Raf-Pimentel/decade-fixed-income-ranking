"""How numbers are written, in one place.

Both outputs, the Markdown and the page, showed the same figures through
their own private copies of these two functions. Two copies is two places to
fix a currency bug, and one of them would eventually be missed.

Anything that is not a number prints as a dash rather than raising: in a
report, a missing figure is information, not a failure.
"""

from __future__ import annotations


def _as_number(value: object) -> float | None:
    """The value as a float, or None if it is not a number at all.

    Booleans are excluded on purpose: `True` is an `int` in Python, and a flag
    printed as "100.00%" would be a quietly wrong report.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def percent(value: object, places: int = 2) -> str:
    """A fraction as a percentage. `0.0004` becomes `0.040%`.

    A negative number too small to survive the rounding prints without its
    sign. `-0.00%` is not a quantity, and a reader who meets it on the page
    cannot tell an artefact of rounding from a broken formatter, which is a
    reason to doubt every other figure beside it. The sign is dropped only
    when the printed digits are all zero, so a fund that genuinely trailed its
    benchmark still shows it.
    """
    number = _as_number(value)
    if number is None:
        return "—"
    text = f"{number * 100:.{places}f}%"
    return text.removeprefix("-") if float(text[:-1]) == 0.0 else text


def money(value: object) -> str:
    """Brazilian reais, abbreviated at the scales that actually occur here."""
    amount = _as_number(value)
    if amount is None:
        return "—"
    if amount >= 1e9:
        return f"R$ {amount / 1e9:.1f} bi"
    if amount >= 1e6:
        return f"R$ {amount / 1e6:.0f} mi"
    return f"R$ {amount:,.0f}"


def count(value: object) -> str:
    """A whole number with Brazilian thousands separators."""
    number = _as_number(value)
    if number is None:
        return "—"
    return f"{int(number):,}".replace(",", ".")
