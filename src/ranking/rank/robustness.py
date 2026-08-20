"""Is the top five real, or is it noise?

With twelve months of daily data the uncertainty around a fund's return per
unit of risk is on the order of ±1.5 — larger than the gaps this ranking would
otherwise be sorting on. Publishing an ordered list of five names as though
the order meant something would be false precision.

So the whole ranking is rebuilt a thousand times, varying the two things that
could reasonably have been different:

- **the data**, by resampling each fund's returns in blocks, which preserves
  the day-to-day persistence that daily resampling would destroy;
- **the opinion**, by jittering the weights inside declared ranges — the fee
  can be worth between 25 and 35, not between 0 and 100.

What gets published is how often each fund survived, not where it landed once.

One caveat is reported alongside, because it would otherwise flatter the
numbers: fees and redemption terms do not move between simulations. A fund
that ranks well largely on cost will look extremely stable, and that stability
is partly mechanical. `appearance_rate_variable_only` re-runs the count using
only the metrics that actually moved.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import polars as pl

from ranking.rank import scoring


def block_bootstrap(returns: np.ndarray, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """Resample a return series in contiguous blocks.

    Drawing single days independently would break the autocorrelation that
    matters here — credit funds post long runs of small positive returns —
    and would make every fund look better behaved than it is.
    """
    length = returns.size
    if length == 0:
        return returns
    size = max(1, min(block_size, length))
    starts = rng.integers(0, length - size + 1, size=int(np.ceil(length / size)))
    return np.concatenate([returns[start : start + size] for start in starts])[:length]


def resample_metrics(
    series: pl.DataFrame,
    order: Sequence[str],
    benchmark_rate: float,
    simulations: int,
    block_size: int,
    seed: int,
) -> dict[str, np.ndarray]:
    """Rebuild the return-based metrics from resampled histories.

    Every fund is resampled with the **same** block indices within a given
    simulation. That is deliberate: funds do not experience independent
    histories, they live through the same weeks, and resampling them
    independently would quietly assume away the fact that they fall together.
    It also happens to be far cheaper, because one index vector serves the
    whole matrix.

    Funds are aligned on their most recent common number of observations. A
    fund that started mid-year contributes what it has, and every fund
    contributes the same count, so a single index vector is meaningful across
    the matrix.
    """
    grouped = series.sort("cnpj_classe", "data").group_by("cnpj_classe", maintain_order=True)
    quotas = {cnpj: group["valor_cota"].to_numpy() for (cnpj,), group in grouped}
    usable = [cnpj for cnpj in order if quotas.get(cnpj) is not None and quotas[cnpj].size > 2]
    if not usable:
        return {}

    length = min(quotas[cnpj].size for cnpj in usable) - 1
    returns = np.vstack([(quotas[cnpj][1:] / quotas[cnpj][:-1] - 1)[-length:] for cnpj in usable])
    # Precomputed once. Looking the position up inside the simulation loop
    # would be a thousand linear scans over a thousand funds.
    slot_of = {cnpj: index for index, cnpj in enumerate(order)}
    columns = np.array([slot_of[cnpj] for cnpj in usable])

    rng = np.random.default_rng(seed)
    size = max(1, min(block_size, length))
    blocks = int(np.ceil(length / size))

    total = np.full((simulations, len(order)), np.nan)
    volatility = np.full((simulations, len(order)), np.nan)
    drawdown = np.full((simulations, len(order)), np.nan)

    for step in range(simulations):
        starts = rng.integers(0, length - size + 1, size=blocks)
        index = np.concatenate([np.arange(start, start + size) for start in starts])[:length]
        drawn = returns[:, index]

        path = np.cumprod(1.0 + drawn, axis=1)
        peak = np.maximum.accumulate(path, axis=1)
        row_total = path[:, -1] - 1.0
        row_vol = drawn.std(axis=1, ddof=1) * np.sqrt(252)
        row_fall = (path / peak - 1.0).min(axis=1)

        total[step, columns] = row_total
        volatility[step, columns] = row_vol
        drawdown[step, columns] = row_fall

    with np.errstate(divide="ignore", invalid="ignore"):
        per_risk = np.where(volatility > 0, (total - benchmark_rate) / volatility, np.nan)

    return {
        "excess_return": total - benchmark_rate,
        "volatility": volatility,
        "max_drawdown": drawdown,
        "return_per_risk": per_risk,
    }


def jitter_weights(
    weights: dict[str, int], ranges: dict[str, int], rng: np.random.Generator
) -> dict[str, float]:
    """Draw a nearby set of weights, renormalised to sum to 100.

    The ranges are declared in configuration rather than open-ended: the point
    is to test whether the answer survives a *reasonable* difference of
    opinion, not whether it survives an arbitrary one.
    """
    drawn = {
        name: max(0.0, weight + rng.uniform(-ranges.get(name, 0), ranges.get(name, 0)))
        for name, weight in weights.items()
    }
    total = sum(drawn.values())
    if total <= 0:
        return {name: float(weight) for name, weight in weights.items()}
    return {name: value * 100 / total for name, value in drawn.items()}


def _top_ids(
    frame: pl.DataFrame,
    weights: dict[str, float],
    metrics_config: dict[str, str],
    group: str,
    top_n: int,
) -> list[str]:
    scored = frame
    for metric, direction in metrics_config.items():
        if metric in scored.columns:
            scored = scoring.peer_percentile(
                scored, metric=metric, group=group, direction=direction
            )
    usable = {name: value for name, value in weights.items() if f"{name}_pct" in scored.columns}
    if not usable:
        return []
    total = sum(usable.values())
    normalised = {name: value * 100 / total for name, value in usable.items()}
    scored = scoring.total_score(scored, _to_int_weights(normalised))
    return scored.sort("score", descending=True).head(top_n)["cnpj_classe"].to_list()


def _to_int_weights(weights: dict[str, float]) -> dict[str, int]:
    """`total_score` insists on weights summing to exactly 100, so rounding is
    settled here rather than left to floating point."""
    rounded = {name: round(value) for name, value in weights.items()}
    drift = 100 - sum(rounded.values())
    if drift and rounded:
        heaviest = max(rounded, key=lambda name: rounded[name])
        rounded[heaviest] += drift
    return rounded


def simulate(
    funds: pl.DataFrame,
    weights: dict[str, int],
    seed: int,
    simulations: int = 1000,
    jitter: dict[str, int] | None = None,
    metrics_config: dict[str, str] | None = None,
    group: str = "peer_group",
    top_n: int = 5,
    varying_metrics: Sequence[str] | None = None,
    metric_draws: dict[str, np.ndarray] | None = None,
) -> pl.DataFrame:
    """Rebuild the ranking many times and count who keeps surviving.

    `metric_draws` optionally carries one resampled column per simulation for
    the metrics derived from the return series. Without it only the weights
    move, which is a weaker test and is reported as such.
    """
    if metrics_config is None:
        metrics_config = {name: "high" for name in weights}
    ranges = jitter or {}
    rng = np.random.default_rng(seed)

    identifiers = funds["cnpj_classe"].to_list()
    appearances = dict.fromkeys(identifiers, 0)
    appearances_variable = dict.fromkeys(identifiers, 0)

    variable = list(varying_metrics or (metric_draws or {}).keys())
    variable_weights = {name: weights[name] for name in weights if name in variable}

    for index in range(simulations):
        frame = funds
        if metric_draws:
            frame = frame.with_columns(
                [
                    pl.Series(name, draws[index % draws.shape[0]])
                    for name, draws in metric_draws.items()
                ]
            )
        drawn = jitter_weights(weights, ranges, rng)
        for cnpj in _top_ids(frame, drawn, metrics_config, group, top_n):
            appearances[cnpj] += 1

        if variable_weights:
            drawn_variable = jitter_weights(variable_weights, ranges, rng)
            for cnpj in _top_ids(frame, drawn_variable, metrics_config, group, top_n):
                appearances_variable[cnpj] += 1

    return pl.DataFrame(
        {
            "cnpj_classe": identifiers,
            "appearance_rate": [appearances[c] / simulations for c in identifiers],
            "appearance_rate_variable_only": [
                appearances_variable[c] / simulations if variable_weights else None
                for c in identifiers
            ],
        }
    )
