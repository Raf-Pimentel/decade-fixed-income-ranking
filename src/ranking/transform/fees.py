"""What a fund charges, measured rather than read off a form.

The administration fee carries the heaviest weight in both profiles, which
makes it the number this project can least afford to get wrong. It arrives in
the CVM statement as a declared field, and for one family of classes that
field is not the price the client pays.

The reason is structural. Under RCVM 175 a manager runs one portfolio and
sells it through feeder classes, each filing its own statement. Some houses
now file a nominal class-level figure there rather than what the investor
actually gives up. Measured against the delivered ranking of 31/12/2025, four
Itaú classes filed 0.040% while charging between 0.45% and 1.81%. The same
classes filed 0.400%, 0.900% and 0.450% a year earlier, and nobody cuts a fee
from 0.900% to 0.040%. See docs/04-a-taxa-e-a-conferencia.md for the evidence.

So the fee is measured instead. A feeder puts nearly all of its money into one
master fund, which means the two quota series are the same portfolio priced
twice. Everything that could make them diverge is the same on both sides
except what the class keeps, so the class ends the period holding a fixed
fraction of what the master made:

    fee = 1 - (class growth / master growth) ** (1 / years)

That holds whatever anyone filed, and it needs nothing but two quota series
and the knowledge of which fund the class buys. The first comes from the daily
report the project already reads; the second from the portfolio composition
file, which names the fund behind each holding.

Two limits are worth stating plainly. The measurement only reaches classes
that are feeders, because a fund that holds bonds directly has nothing to be
compared against; those keep the declared value, which is correct for most of
the market. And when a feeder holds cash or a second fund alongside its
master, the gap carries that allocation too, so the figure becomes a ceiling
rather than an exact fee. The share threshold is what bounds that error, and
it is declared in configuration rather than buried here.
"""

from __future__ import annotations

import polars as pl

LINK_COLUMNS = ["cnpj_classe", "cnpj_master", "share"]


def master_of(holdings: pl.DataFrame, min_share: float) -> pl.DataFrame:
    """The single fund a class is a wrapper for, where there is one.

    A class qualifies when its largest fund holding is at least `min_share` of
    everything it holds in funds. Below that it is allocating between funds
    rather than wrapping one, and the difference between its return and any
    single holding's would be allocation as much as cost.
    """
    if holdings.is_empty():
        return pl.DataFrame(
            schema={"cnpj_classe": pl.Utf8, "cnpj_master": pl.Utf8, "share": pl.Float64}
        )

    totals = holdings.group_by("cnpj_classe").agg(pl.col("valor").sum().alias("total"))
    biggest = (
        holdings.group_by("cnpj_classe", "cnpj_investido")
        .agg(pl.col("valor").sum().alias("valor"))
        .sort("valor", descending=True)
        .group_by("cnpj_classe")
        .first()
    )
    return (
        biggest.join(totals, on="cnpj_classe")
        .with_columns((pl.col("valor") / pl.col("total")).alias("share"))
        .filter(pl.col("total") > 0)
        .filter(pl.col("share") >= min_share)
        .select(
            pl.col("cnpj_classe"),
            pl.col("cnpj_investido").alias("cnpj_master"),
            pl.col("share"),
        )
        .sort("cnpj_classe")
    )


def measured(
    series: pl.DataFrame,
    links: pl.DataFrame,
    business_days_per_year: int,
    min_overlap_days: int = 60,
) -> pl.DataFrame:
    """The annual fee each linked class charged over the days it shares with its master.

    A fee is charged on assets day after day, so it compounds, and the class
    keeps a constant fraction of the master's growth rather than a constant
    number of percentage points. The annual rate is therefore the ratio of the
    two growth factors raised to the reciprocal of the elapsed years, which is
    what makes a fee measured over six months equal to the same fee measured
    over two. Taking the plain difference and dividing by the years would give
    a figure that drifts with the length of the window.

    A pair with too little shared history is left out rather than
    extrapolated, and so is a class that appears to have beaten its master: a
    fee below zero is a bad link or noise, and publishing it would hand the
    best possible cost percentile to a measurement error.
    """
    empty = pl.DataFrame(
        schema={"cnpj_classe": pl.Utf8, "taxa_adm_medida": pl.Float64, "dias_medidos": pl.Int64}
    )
    if links.is_empty() or series.is_empty():
        return empty

    quotas = series.select("cnpj_classe", "data", "valor_cota")
    pairs = links.select("cnpj_classe", "cnpj_master")

    joined = (
        pairs.join(quotas, on="cnpj_classe")
        .join(
            quotas.rename({"cnpj_classe": "cnpj_master", "valor_cota": "cota_master"}),
            on=["cnpj_master", "data"],
        )
        .sort("cnpj_classe", "data")
    )
    if joined.is_empty():
        return empty

    out = (
        joined.group_by("cnpj_classe")
        .agg(
            pl.len().alias("dias_medidos"),
            pl.col("valor_cota").first().alias("classe_inicio"),
            pl.col("valor_cota").last().alias("classe_fim"),
            pl.col("cota_master").first().alias("master_inicio"),
            pl.col("cota_master").last().alias("master_fim"),
        )
        .filter(pl.col("dias_medidos") >= min_overlap_days)
        .filter((pl.col("classe_inicio") > 0) & (pl.col("master_inicio") > 0))
        .with_columns(
            (
                (pl.col("classe_fim") / pl.col("classe_inicio"))
                / (pl.col("master_fim") / pl.col("master_inicio"))
            ).alias("retencao"),
            ((pl.col("dias_medidos") - 1) / business_days_per_year).alias("anos"),
        )
        .filter((pl.col("retencao") > 0) & (pl.col("anos") > 0))
        .with_columns((1.0 - pl.col("retencao") ** (1.0 / pl.col("anos"))).alias("taxa_adm_medida"))
        .filter(pl.col("taxa_adm_medida") >= 0)
        .select("cnpj_classe", "taxa_adm_medida", "dias_medidos")
        .sort("cnpj_classe")
    )
    return out if not out.is_empty() else empty


def reconcile(funds: pl.DataFrame, measurements: pl.DataFrame) -> pl.DataFrame:
    """Settle on one fee per fund, erring against the fund every time.

    Three rules, and each of them costs a fund rather than rewards it.

    Where both numbers exist, the **higher** wins. A class cannot plausibly
    charge less than its own manager filed for it, so a measurement that comes
    out lower is noise or the sleeve a feeder holds outside its master, not a
    discount. Believing a fee that is too low promotes a fund into a top five
    it did not earn, and cost is the heaviest weight there is.

    A class that invests through other funds and could **not** be measured is
    left with no fee at all. The filed field is unreliable precisely for that
    kind of class, so for them it is not evidence, and the rule that already
    refuses to rank what cannot be priced takes them out. This is the same
    treatment a declared zero gets, for the same reason.

    Everything else keeps what it filed. The problem is one family of classes,
    not the market, and blanking the fee of a fund that holds its assets
    directly would discard most of the universe to repair a minority.

    Both numbers travel onward either way, so the delivery can show what was
    declared next to what was charged.
    """
    if "taxa_adm_declarada" not in funds.columns:
        funds = funds.with_columns(pl.col("taxa_adm").alias("taxa_adm_declarada"))

    if measurements.is_empty() or "taxa_adm_medida" not in measurements.columns:
        funds = funds.with_columns(pl.lit(None, dtype=pl.Float64).alias("taxa_adm_medida"))
    else:
        funds = funds.join(
            measurements.select("cnpj_classe", "taxa_adm_medida"), on="cnpj_classe", how="left"
        ).with_columns(
            pl.max_horizontal("taxa_adm", "taxa_adm_medida").alias("taxa_adm"),
        )

    if "classe_cotas" not in funds.columns:
        return funds
    unverifiable = (pl.col("classe_cotas").str.strip_chars().str.to_uppercase() == "S") & pl.col(
        "taxa_adm_medida"
    ).is_null()
    return funds.with_columns(
        pl.when(unverifiable).then(None).otherwise(pl.col("taxa_adm")).alias("taxa_adm")
    )
