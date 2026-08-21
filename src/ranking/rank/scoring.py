"""Turning ten unrelated numbers into one score.

The central choice is that a fund is compared **only against funds like it**.
In 2025 the funds that returned most were the ones that took most credit risk,
so a ranking by return — or even by return per unit of risk measured across
the whole universe — would hand back the five riskiest names and call them
best. Their problem simply had not arrived yet.

Comparing inside the ANBIMA category asks the question that can actually be
answered from a price series: is this fund good *for what it is*? The trade
between categories is then made explicitly, by the weights, where it can be
argued with.
"""

from __future__ import annotations

import polars as pl

GLOBAL_PEER_GROUP = "(universo inteiro)"


def merge_small_groups(funds: pl.DataFrame, group: str, min_size: int) -> pl.DataFrame:
    """Mark funds whose category is too small to be a peer group.

    A percentile among four funds is noise dressed as information. Those funds
    are compared against the whole eligible universe instead, and the output
    says which of the two happened — inventing a peer group out of four names
    would be worse than admitting there isn't one.
    """
    sizes = funds.group_by(group).len()
    big = sizes.filter(pl.col("len") >= min_size)[group].to_list()
    return funds.with_columns(
        pl.when(pl.col(group).is_in(big))
        .then(pl.col(group))
        .otherwise(pl.lit(GLOBAL_PEER_GROUP))
        .alias("peer_group_effective")
    )


def winsorise(frame: pl.DataFrame, metric: str, lower: float, upper: float) -> pl.DataFrame:
    """Clip the extremes before ranking.

    One fund with a mis-stated quota should not be able to define the top of
    the scale for everybody else. Clipping rather than dropping keeps the fund
    in the ranking, where it can be seen.
    """
    low = frame[metric].quantile(lower, interpolation="linear")
    high = frame[metric].quantile(upper, interpolation="linear")
    if low is None or high is None:
        return frame
    return frame.with_columns(pl.col(metric).clip(low, high))


def peer_percentile(frame: pl.DataFrame, metric: str, group: str, direction: str) -> pl.DataFrame:
    """Position of each fund within its peer group, from 0 (worst) to 1 (best).

    `direction` says which end is good: "high" for return, "low" for cost. Get
    that backwards and the ranking recommends the most expensive funds while
    looking entirely plausible.

    Funds pooled into the global group are ranked against the entire frame,
    not against the other strays — which is the whole point of pooling them.
    """
    if direction not in {"high", "low"}:
        raise ValueError(f"direction must be 'high' or 'low', got {direction!r}")
    descending = direction == "low"
    column = f"{metric}_pct"

    ranked = frame.with_columns(
        pl.col(metric).rank(method="average", descending=descending).over(group).alias("_rank"),
        pl.len().over(group).alias("_size"),
        pl.col(metric).rank(method="average", descending=descending).alias("_rank_all"),
        pl.len().alias("_size_all"),
    )
    # A group of one has no spread to measure; 0.5 says "no information" rather
    # than crowning it.
    pooled = pl.col(group) == GLOBAL_PEER_GROUP
    rank = pl.when(pooled).then(pl.col("_rank_all")).otherwise(pl.col("_rank"))
    size = pl.when(pooled).then(pl.col("_size_all")).otherwise(pl.col("_size"))
    return ranked.with_columns(
        pl.when(size > 1).then((rank - 1) / (size - 1)).otherwise(pl.lit(0.5)).alias(column)
    ).drop("_rank", "_size", "_rank_all", "_size_all")


def dispersion(frame: pl.DataFrame, metric: str) -> float:
    """How much a metric actually varies across the funds being compared.

    Measured as the share of funds that do *not* sit on the single most common
    value, which is the form of the question that matters for a ranking: a
    percentile can only separate funds that differ, and ties all receive the
    same average rank whatever the weight attached to them.
    """
    values = frame[metric].drop_nulls()
    if values.len() == 0:
        return 0.0
    counts = values.value_counts().get_column("count")
    largest_tie = counts.max()
    if not isinstance(largest_tie, int):  # pragma: no cover - polars always counts as int
        return 0.0
    return 1.0 - largest_tie / values.len()


def effective_weights(
    frame: pl.DataFrame, weights: dict[str, int], min_dispersion: float
) -> tuple[dict[str, int], list[str]]:
    """Redistribute weight away from metrics that cannot separate anything.

    Eligibility and scoring answer different questions, and a metric can be
    load-bearing for the first and empty for the second. The liquidity profile
    admits only funds that pay out within a day, so by the time its funds are
    scored almost all of them settle same-day: redemption speed has already
    done its work as a filter and has nothing left to say as a criterion.
    Every fund ties, every percentile comes back at one half, and the weight
    attached to it is subtracted from the ones that could still discriminate.

    Rather than quietly carry a dead term, the weight is moved to the metrics
    that do vary, in proportion to what they already carried, and the metric is
    named in the output. This is a rule about the shape of the data, applied
    identically to every profile and every reference date — not a judgement
    about any particular number, which is what keeps the weights themselves
    frozen.
    """
    live = {
        name: weight
        for name, weight in weights.items()
        if name in frame.columns and dispersion(frame, name) >= min_dispersion
    }
    inert = [name for name in weights if name not in live]
    if not inert or not live:
        return dict(weights), []

    total = sum(live.values())
    scaled = {name: weight * 100 / total for name, weight in live.items()}
    rounded = {name: round(value) for name, value in scaled.items()}
    drift = 100 - sum(rounded.values())
    if drift:
        heaviest = max(rounded, key=lambda name: rounded[name])
        rounded[heaviest] += drift
    return rounded, inert


def total_score(frame: pl.DataFrame, weights: dict[str, int]) -> pl.DataFrame:
    """Weighted sum of the percentiles, on a 0 to 100 scale.

    Both checks below exist because the failure they prevent is silent. Weights
    that do not sum to 100 still produce a ranking, just one whose scores mean
    something different from what the documentation claims. A weight naming a
    metric that was never computed would simply be skipped.
    """
    total = sum(weights.values())
    if total != 100:
        raise ValueError(f"weights must sum to 100, got {total}")

    missing = [name for name in weights if f"{name}_pct" not in frame.columns]
    if missing:
        raise KeyError(f"no percentile column for weighted metrics: {sorted(missing)}")

    expression = pl.lit(0.0)
    for name, weight in weights.items():
        expression = expression + pl.col(f"{name}_pct").fill_null(0.5) * weight
    return frame.with_columns(expression.alias("score"))
