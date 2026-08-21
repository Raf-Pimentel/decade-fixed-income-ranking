"""Choosing five funds rather than five scores.

A score ranks funds one at a time. A list of five is consumed all at once, by
someone who will hold all of them, and those are different questions. The gap
between them shows up in the Brazilian market in a specific and very common
shape: one manager runs a single portfolio and sells it through a row of
distribution wrappers, each a separate class with its own name, its own CNPJ
and its own entry in the CVM registry. Caixa alone offers a dozen of them over
one fixed-income portfolio — Executivo, Clássico, Personal, Investidor,
Especial — and every one of them is legitimately eligible, and every one earns
nearly the same score, because they are nearly the same fund.

Scoring alone therefore returns a list whose length overstates its content: a
top five holding two wrappers of one portfolio offers four exposures, and the
reader has no way to tell. What follows walks the ranked funds in order and
accepts one only if it adds something to what has already been accepted.

**What counts as the same fund.** Two conditions together, and neither alone.
The funds must be run by the same manager, and the difference between their
daily returns must barely move — measured as the annualised volatility of that
difference, the tracking difference. Two wrappers of one portfolio differ only
by their fee, which is a constant daily drag and contributes no variance, so
their tracking difference is near zero. Two genuinely different funds from
different houses do not qualify however similar they look.

That second condition is what the obvious choice gets wrong. Correlation of
daily returns cannot do this job in a post-fixed market: every fund tracking
the overnight rate correlates above 0.99 with every other one, because they
are all following the same curve. Measured on this universe, a correlation
threshold high enough to be meaningful still marks half the funds as
duplicates of something. The tracking difference asks the right question —
*how much do these two disagree*, rather than *do they move together* — and it
separates a Selic fund from another house's Selic fund while still collapsing
two names for one portfolio.

Nothing is hidden. A fund passed over this way is published beside the list,
named, with the fund it duplicates and the tracking difference between them,
so that a reader can see the sixth name was reached for a reason.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Displacement:
    """A fund the score reached and the distinctness rule kept out."""

    cnpj_classe: str
    duplicate_of: str
    tracking_difference: float


def pick_distinct(
    ordered: Sequence[str],
    duplicates: Mapping[str, Mapping[str, float]],
    top_n: int,
) -> tuple[list[str], list[Displacement]]:
    """Take the first `top_n` funds that are distinguishable from each other.

    Order is never rearranged. The ranking decides who is considered first and
    this decides only whether a candidate adds anything to what is already on
    the list, so a fund is never promoted over a better-ranked one — it is
    reached because the better-ranked one turned out to be a name for something
    already held.

    A fund with no usable series is accepted rather than rejected: the absence
    of evidence that it duplicates something is not evidence that it does.
    """
    chosen: list[str] = []
    displaced: list[Displacement] = []

    for candidate in ordered:
        if len(chosen) >= top_n:
            break
        twins = duplicates.get(candidate, {})
        matched = [(held, twins[held]) for held in chosen if held in twins]
        if not matched:
            chosen.append(candidate)
            continue
        closest, distance = min(matched, key=lambda pair: pair[1])
        displaced.append(
            Displacement(
                cnpj_classe=candidate,
                duplicate_of=closest,
                tracking_difference=round(distance, 6),
            )
        )
    return chosen, displaced
