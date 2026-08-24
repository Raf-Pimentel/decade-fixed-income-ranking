"""Is the top five real, or is it noise?

With twelve months of daily data the uncertainty around a fund's return per
unit of risk is on the order of +/-1.5 - larger than the gaps this ranking
would otherwise be sorting on. Publishing an ordered list of five names as
though the order meant something would be false precision.

So the whole ranking is rebuilt a thousand times, varying the two things that
could reasonably have been different:

- **the data**, by resampling each fund's returns in blocks, which preserves
  the day-to-day persistence that daily resampling would destroy;
- **the opinion**, by jittering the weights inside declared ranges - the fee
  can be worth between 25 and 35, not between 0 and 100.

What gets published is how often each fund survived, not where it landed once.

Three properties of the resampling are what make that survival count mean
something, and each exists because the obvious alternative quietly inflates it.

**Every fund draws its own blocks.** The quantity being estimated is how much
of one fund's advantage over another is luck of the sample, which is an
idiosyncratic question. Handing every fund the same resampled calendar
preserves the market's co-movement, which sounds like the conservative choice
and is the opposite: it moves the whole cross-section together, leaves the
relative order almost untouched, and returns survival rates near one hundred
per cent for a ranking nobody has actually stressed. What it costs is that a
simulated year contains no common crash - stated here rather than hidden, and
the cheaper of the two errors.

**The benchmark is resampled with the fund.** Excess return is a difference
between two compounded series, so both sides have to be compounded over the
same days. Measuring a resampled fund year against the calendar year's CDI
biases every excess return by whatever the resampling did to the window, and
because return per unit of risk divides that difference by volatility, a bias
that would cancel in a ranking on excess alone does not cancel there. It
reorders, in favour of the most volatile funds.

**Funds keep their own history length.** A fund that began mid-window has
fewer observations than one that did not, and truncating the panel to the
shortest of them would discard a fifth of everyone's evidence to accommodate
the newest arrival.

Two caveats travel with the numbers, because both would otherwise flatter
them. Fees and redemption terms do not move between simulations, so a fund
ranked largely on cost looks extremely stable and part of that stability is
mechanical; `appearance_rate_variable_only` re-runs the count on the metrics
that actually moved. And reshuffling what happened never creates what did not:
if no fund suffered a credit event inside the window, no simulation will
invent one. This measures sampling luck, not tail risk.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import polars as pl

from ranking.rank import scoring


def block_bootstrap(returns: np.ndarray, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """Resample a return series in contiguous blocks.

    Drawing single days independently would break the autocorrelation that
    matters here, because credit funds post long runs of small positive
    returns,
    and would make every fund look better behaved than it is.
    """
    length = returns.size
    if length == 0:
        return returns
    size = max(1, min(block_size, length))
    starts = rng.integers(0, length - size + 1, size=int(np.ceil(length / size)))
    return np.concatenate([returns[start : start + size] for start in starts])[:length]


def _aligned_panel(
    series: pl.DataFrame,
    order: Sequence[str],
    benchmark: pl.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Lay every fund's returns out as one rectangle, left-aligned and padded.

    Each row holds one fund's daily returns from its own first observation
    onwards, followed by padding that carries no value. The benchmark is laid
    out the same way and matched to that fund's own dates rather than to a
    shared calendar, so that a given column of both rows always refers to the
    same day.
    """
    grouped = series.sort("cnpj_classe", "data").group_by("cnpj_classe", maintain_order=True)
    rates = dict(zip(benchmark["data"].to_list(), benchmark["taxa"].to_list(), strict=True))
    slot_of = {cnpj: index for index, cnpj in enumerate(order)}

    rows: list[tuple[int, np.ndarray, np.ndarray]] = []
    for (cnpj,), group in grouped:
        if cnpj not in slot_of:
            continue
        quotas = group["valor_cota"].to_numpy()
        if quotas.size <= 2:
            continue
        days = group["data"].to_list()[1:]
        rows.append(
            (
                slot_of[cnpj],
                quotas[1:] / quotas[:-1] - 1,
                np.array([rates.get(day, 0.0) for day in days], dtype=np.float64),
            )
        )

    if not rows:
        empty = np.zeros((0, 0))
        return empty, empty, np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)

    width = max(fund.size for _, fund, _ in rows)
    returns = np.full((len(rows), width), np.nan)
    rate_panel = np.full((len(rows), width), np.nan)
    lengths = np.empty(len(rows), dtype=np.int64)
    columns = np.empty(len(rows), dtype=np.int64)
    for row, (slot, fund, rate) in enumerate(rows):
        returns[row, : fund.size] = fund
        rate_panel[row, : rate.size] = rate
        lengths[row] = fund.size
        columns[row] = slot
    return returns, rate_panel, lengths, columns


def resample_metrics(
    series: pl.DataFrame,
    order: Sequence[str],
    benchmark: pl.DataFrame,
    simulations: int,
    block_size: int,
    seed: int,
) -> dict[str, np.ndarray]:
    """Rebuild the return-based metrics from resampled histories.

    Returns one matrix per metric, shaped simulations by funds, carrying a
    column for every entry of `order`. Drawing once for the whole eligible set
    lets each profile slice out the funds it can reach without redrawing, so
    the two profiles are looking at the same uncertainty rather than at two
    independent inventions of it.
    """
    returns, rates, lengths, columns = _aligned_panel(series, order, benchmark)
    if returns.size == 0:
        return {}

    funds, width = returns.shape
    size = max(1, min(block_size, int(lengths.min())))
    blocks = int(np.ceil(width / size))
    # A row is only as long as its own history. Everything past that is
    # padding, and is excluded from every statistic rather than counted as a
    # stretch of calm the fund never lived through.
    live = np.arange(width)[None, :] < lengths[:, None]
    highest = np.maximum(lengths - size + 1, 1)
    last = (lengths - 1)[:, None]
    offsets = np.arange(size)[None, None, :]

    rng = np.random.default_rng(seed)
    shape = (simulations, len(order))
    volatility = np.full(shape, np.nan)
    drawdown = np.full(shape, np.nan)
    excess = np.full(shape, np.nan)

    for step in range(simulations):
        starts = (rng.random((funds, blocks)) * highest[:, None]).astype(np.int64)
        index = (starts[:, :, None] + offsets).reshape(funds, -1)[:, :width]
        index = np.minimum(index, last)

        drawn = np.where(live, np.take_along_axis(returns, index, axis=1), np.nan)
        drawn_rates = np.where(live, np.take_along_axis(rates, index, axis=1), np.nan)

        path = np.nancumprod(1.0 + drawn, axis=1)
        peak = np.maximum.accumulate(path, axis=1)
        fund_total = np.nanprod(1.0 + drawn, axis=1) - 1.0
        benchmark_total = np.nanprod(1.0 + drawn_rates, axis=1) - 1.0

        excess[step, columns] = fund_total - benchmark_total
        volatility[step, columns] = np.nanstd(drawn, axis=1, ddof=1) * np.sqrt(252)
        drawdown[step, columns] = (path / peak - 1.0).min(axis=1)

    with np.errstate(divide="ignore", invalid="ignore"):
        per_risk = np.where(volatility > 0, excess / volatility, np.nan)

    return {
        "excess_return": excess,
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
    duplicates: Mapping[str, frozenset[str]] | None = None,
) -> list[str]:
    """The list this run of the ranking would publish.

    The same distinctness rule that shapes the published list applies here.
    Counting survival on a list built by a different rule than the one that
    produced the answer would measure the stability of something nobody is
    being shown.
    """
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
    ordered = scored.sort("score", descending=True)["cnpj_classe"].to_list()
    if not duplicates:
        return ordered[:top_n]

    chosen: list[str] = []
    for candidate in ordered:
        if len(chosen) >= top_n:
            break
        twins = duplicates.get(candidate, frozenset())
        if not any(accepted in twins for accepted in chosen):
            chosen.append(candidate)
    return chosen


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
    duplicates: Mapping[str, frozenset[str]] | None = None,
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
        for cnpj in _top_ids(frame, drawn, metrics_config, group, top_n, duplicates):
            appearances[cnpj] += 1

        if variable_weights:
            drawn_variable = jitter_weights(variable_weights, ranges, rng)
            for cnpj in _top_ids(frame, drawn_variable, metrics_config, group, top_n, duplicates):
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
