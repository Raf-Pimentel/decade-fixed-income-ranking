"""Choosing five funds rather than five scores.

A score ranks funds one at a time; a list of five is held all at once. One
manager routinely runs a single portfolio and sells it through a row of
distribution wrappers. Caixa offers a dozen over one fixed-income portfolio.
Each is a separate class, each is legitimately eligible, and each earns
nearly the same score. A top five holding two of them offers four exposures
without saying so.

Two funds count as one when the same manager runs both **and** their tracking
difference, meaning the annualised volatility of the difference between their
daily returns, is near zero. Two wrappers of one portfolio differ only by their
fee, a constant drag that contributes no variance.

Correlation cannot do this job here, which is why it is not used: every
post-fixed fund follows the same overnight curve and correlates above 0.99
with every other, so a threshold high enough to catch a twin marks half this
universe as duplicated. The tracking difference asks *how much do these two
disagree* rather than *do they move together*. See D-040.
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
    the list, so a fund is never promoted over a better-ranked one. It is
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
