"""Deciding whether a run can be trusted at all.

Two brakes, doing different jobs.

The **quarantine limit** catches a file that arrived broken: if a twentieth of
it had to be thrown away, whatever is left is not a sample worth ranking.

The **funnel comparison** catches the subtler failure, a run that produces
perfectly valid rows, just the wrong number of them. A join that silently
matched half the universe raises nothing, passes every schema, and yields a
confident ranking of the wrong funds. The only way to notice is to have
written down, in advance, how many funds should survive each step.

One lesson is baked in here. During phase 3 a duplicated key in the CVM
registry inflated the universe by 2%, and this comparison **passed**, because
2% fits inside a 3% tolerance. So a percentage band is necessary and not
sufficient. Exact invariants, like a join never changing a row count, belong
next to the operation itself, not here.
"""

from __future__ import annotations

from dataclasses import dataclass


class TooMuchQuarantinedError(RuntimeError):
    """So much of the input was unusable that ranking it would be misleading."""


class FunnelDeviationError(RuntimeError):
    """The universe is a different size than it should be. Investigate first."""


def assert_quarantine_within_limit(total_rows: int, quarantined_rows: int, limit: float) -> None:
    """Stop the run when too large a share of the input had to be discarded.

    Delivering no ranking is a recoverable problem. Delivering a ranking built
    on a fifth of the funds, with nothing on screen saying so, is not.
    """
    if total_rows <= 0:
        return
    share = quarantined_rows / total_rows
    if share > limit:
        raise TooMuchQuarantinedError(
            f"{quarantined_rows:,} of {total_rows:,} rows quarantined ({share:.1%}), "
            f"above the {limit:.0%} limit. Something changed at the source; "
            "look at the quarantine file before rerunning."
        )


@dataclass(frozen=True)
class FunnelStep:
    name: str
    observed: int
    expected: int

    @property
    def deviation(self) -> float:
        if self.expected == 0:
            return 0.0 if self.observed == 0 else 1.0
        return (self.observed - self.expected) / self.expected


@dataclass(frozen=True)
class FunnelReport:
    steps: list[FunnelStep]
    tolerance: float

    @property
    def deviations(self) -> dict[str, float]:
        """Only the steps that drifted beyond the tolerance."""
        return {
            step.name: step.deviation for step in self.steps if abs(step.deviation) > self.tolerance
        }

    @property
    def ok(self) -> bool:
        return not self.deviations

    def to_markdown(self) -> str:
        lines = [
            "# Data quality: the eligibility funnel",
            "",
            f"Tolerance: {self.tolerance:.0%}. "
            f"Verdict: **{'within baseline' if self.ok else 'DEVIATION, investigate'}**.",
            "",
            "| Step | Observed | Baseline | Deviation | |",
            "|---|---:|---:|---:|:--|",
        ]
        for step in self.steps:
            flag = "ok" if abs(step.deviation) <= self.tolerance else "**off**"
            lines.append(
                f"| {step.name} | {step.observed:,} | {step.expected:,} "
                f"| {step.deviation:+.2%} | {flag} |"
            )
        if not self.ok:
            lines += [
                "",
                "A step outside the band means either the source changed or the "
                "pipeline broke. Both are worth understanding before publishing "
                "a ranking.",
            ]
        return "\n".join(lines) + "\n"

    def raise_if_off(self) -> None:
        if not self.ok:
            worst = max(self.deviations.items(), key=lambda item: abs(item[1]))
            raise FunnelDeviationError(
                f"eligibility funnel drifted from the baseline: {worst[0]} is "
                f"{worst[1]:+.1%} off. Investigate before publishing."
            )


def compare_funnel(
    observed: dict[str, int], expected: dict[str, int], tolerance: float
) -> FunnelReport:
    """Line up what this run produced against what was measured in advance."""
    steps = [
        FunnelStep(name=name, observed=count, expected=expected[name])
        for name, count in observed.items()
        if name in expected
    ]
    return FunnelReport(steps=steps, tolerance=tolerance)
