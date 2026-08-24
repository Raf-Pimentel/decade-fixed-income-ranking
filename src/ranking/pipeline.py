"""The whole thing, in one importable function.

`run(reference_date=...)` is the entire programme. The command line is a thin
wrapper over it, and another team can import it directly. That is the point of
the exercise: the ranking has to be usable without anyone explaining it first.

Point-in-time is enforced at three separate places: when the daily report is
validated, when the statement in force is chosen, and again when the panel is
built. That looks like belt and braces because it is. A single row from after
the reference date would not raise anything. It would simply make the backtest
in phase 5.5 quietly optimistic, which is the one failure this project cannot
afford.
"""

from __future__ import annotations

import calendar
import datetime as dt
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

import numpy as np
import polars as pl

from ranking import config
from ranking.contracts import quality, schemas
from ranking.extract import http, manifest, readers
from ranking.publish import html, writers
from ranking.rank import eligibility, robustness, scoring, selection
from ranking.transform import metrics, panel, universe

BUSINESS_DAYS_PER_YEAR = 252


@dataclass
class RunResult:
    payload: schemas.RankingOutput
    funnel: quality.FunnelReport
    max_observation_date: dt.date
    output_dir: Path
    quarantined_share: float = 0.0
    notes: list[str] = field(default_factory=list)
    # Who each profile could have chosen from. The backtest draws its random
    # portfolios from exactly this set, so that the comparison is against the
    # choices the method actually had, not against a different universe.
    eligible_by_profile: dict[str, list[str]] = field(default_factory=dict)
    # The quotas of the funds that were ranked.
    series: pl.DataFrame | None = None
    # Every validated quota in the window, for every fund that published one,
    # whether or not it was eligible. Measuring what happened after a cut date
    # has to read from here: a fund chosen in March and no longer eligible in
    # December still had a return, and reading its outcome from the eligible
    # set would quietly drop exactly the funds whose disappearance is the
    # result worth knowing.
    #
    # Carries the three columns a forward return is computed from and nothing
    # else. The full panel is millions of rows and the out-of-sample test holds
    # one of these open while building another, which is the largest thing this
    # single-node design is ever asked to keep in memory at once.
    all_series: pl.DataFrame | None = None
    # The benchmark's daily rates over the same window, so that anything
    # measured downstream compounds it over the same days as the funds.
    benchmark_daily: pl.DataFrame | None = None
    # The admin fee of every fund that was ranked. The out-of-sample test uses
    # it to draw a control group matched on cost, which is how the part of the
    # result that is fee arithmetic gets separated from the part that is not.
    fees: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Gathering the inputs
# ---------------------------------------------------------------------------


@dataclass
class Inputs:
    daily: pl.DataFrame
    registry: pl.DataFrame
    statement: pl.DataFrame
    factsheet: pl.DataFrame
    cdi: pl.DataFrame
    manifest: dict[str, object] = field(default_factory=dict)


def _months_between(start: dt.date, end: dt.date) -> list[tuple[int, int]]:
    months: list[tuple[int, int]] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def _extract(archive: Path, member: str, destination: Path) -> Path | None:
    """Pull one member out of a zip onto disk, so the ordinary readers can be
    used on it. Extracting rather than reading in memory keeps a single code
    path for files that arrive zipped and files that do not."""
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / member
    if target.exists():
        return target
    with zipfile.ZipFile(archive) as bundle:
        if member not in bundle.namelist():
            return None
        target.write_bytes(bundle.read(member))
    return target


def _read_member(
    archive: Path,
    member: str,
    unpacked: Path,
    read: Callable[[Path], pl.DataFrame],
) -> pl.DataFrame | None:
    path = _extract(archive, member, unpacked)
    return None if path is None else read(path)


def _parsed(
    cache_dir: Path,
    name: str,
    entry: manifest.ManifestEntry,
    read: Callable[[], pl.DataFrame | None],
) -> Path | None:
    """The parsed form of one monthly file, kept beside the archive it came from.

    Parsing is the expensive half of a run. The daily reports arrive as some
    280 MB of latin-1, semicolon-separated text, and turning that into typed
    columns costs far more than the download does once the archives are on
    disk. Each month is parsed once and written back as Parquet under a name
    carrying the source file's own SHA-256, so the cache is keyed by the bytes
    that produced it.

    That key is what makes the cache safe rather than merely fast. The CVM
    restates by overwriting a published file in place, without versioning it;
    a restated archive hashes differently, misses the cache, and is parsed
    again. A cache keyed on the file name would serve yesterday's numbers
    forever and never say so.

    A path comes back rather than a table, and that is the point of the
    function as much as the caching is. Twelve months of daily reports held as
    twelve decoded frames while a thirteenth is being decoded is the peak this
    pipeline has to survive, and it is the only place where a single-node
    design would run out of room first. Handing back the file lets each month
    be released as soon as it is written, and lets the panel be assembled from
    the columnar form in one pass instead of thirteen.
    """
    store = cache_dir / "parsed"
    store.mkdir(parents=True, exist_ok=True)
    target = store / f"{name}.{entry.sha256[:16]}.parquet"
    if target.exists():
        return target
    frame = read()
    if frame is None:
        return None
    frame.write_parquet(target)
    return target


def _load_offline(input_dir: Path) -> Inputs:
    """Read a frozen slice from disk, for tests and for reruns without network."""
    empty = pl.DataFrame(
        schema={
            "cnpj_classe": pl.String,
            "taxa_adm": pl.Float64,
            "dias_resgate": pl.Int64,
            "aplicacao_minima": pl.Float64,
        }
    )
    factsheet_path = input_dir / "factsheet.csv"
    names = [
        "daily_report.csv",
        "registry_class.csv",
        "registry_fund.csv",
        "statement.csv",
        "cdi.json",
    ]
    return Inputs(
        daily=readers.read_daily_report(input_dir / "daily_report.csv"),
        registry=readers.read_registry(
            input_dir / "registry_class.csv", input_dir / "registry_fund.csv"
        ),
        statement=readers.read_statement(input_dir / "statement.csv"),
        factsheet=readers.read_factsheet(factsheet_path) if factsheet_path.exists() else empty,
        cdi=readers.read_cdi(input_dir / "cdi.json"),
        # An offline run is still a run, and it still has to be provable months
        # later. Hashing what was read costs nothing and closes the gap.
        manifest={
            name: manifest.sha256(input_dir / name) for name in names if (input_dir / name).exists()
        },
    )


def _download(
    sources: dict[str, config.Source],
    transfer: config.TransferSettings,
    start: dt.date,
    end: dt.date,
    cache_dir: Path,
) -> Inputs:
    downloader = http.Downloader(transfer.download)
    known = manifest.load(cache_dir / "manifest.json")
    entries: dict[str, manifest.ManifestEntry] = dict(known)

    def fetch(name: str, **kwargs: object) -> Path:
        source = sources[name]
        url = http.resolve_url(source.url, **kwargs)  # type: ignore[arg-type]
        filename = http.resolve_url(source.filename, **kwargs)  # type: ignore[arg-type]
        target = cache_dir / filename
        result = downloader.fetch(url, target, known=known.get(filename))
        entries[filename] = result.entry
        return target

    unpacked = cache_dir / "unpacked"
    months = _months_between(start, end)

    daily_parts: list[Path] = []
    for year, month in months:
        stem = f"inf_diario_fi_{year}{month:02d}"
        archive = fetch("daily_report", year=year, month=month)
        part = _parsed(
            cache_dir,
            stem,
            entries[http.resolve_url(sources["daily_report"].filename, year=year, month=month)],
            partial(_read_member, archive, f"{stem}.csv", unpacked, readers.read_daily_report),
        )
        if part is not None:
            daily_parts.append(part)
    # Assembled from the columnar files in a single pass. Every month shares
    # one schema by construction, so the panel is a scan rather than a stack of
    # frames held open at once.
    daily = pl.scan_parquet(daily_parts).collect()

    registry_zip = fetch("registry")
    classes = _extract(registry_zip, "registro_classe.csv", unpacked)
    funds_file = _extract(registry_zip, "registro_fundo.csv", unpacked)
    if classes is None or funds_file is None:
        raise RuntimeError("the CVM registry archive is missing its expected members")
    registry = readers.read_registry(classes, funds_file)

    # A statement stays in force until the fund files a new one, so the window
    # alone does not bound which files matter: a fund that filed in 2024 and
    # never refiled is still governed by that filing throughout 2025. Every
    # year the window touches is fetched, plus the year before it, which is
    # what keeps a fund that simply had nothing new to say from looking as
    # though it had never disclosed anything at all.
    years = sorted({year for year, _ in months} | {start.year - 1})
    statement = pl.concat(
        [readers.read_statement(fetch("statement", year=year)) for year in years],
        how="diagonal",
    )

    factsheet_parts: list[Path] = []
    for year, month in months:
        stem = f"lamina_fi_{year}{month:02d}"
        archive = fetch("factsheet", year=year, month=month)
        part = _parsed(
            cache_dir,
            stem,
            entries[http.resolve_url(sources["factsheet"].filename, year=year, month=month)],
            partial(_read_member, archive, f"{stem}.csv", unpacked, readers.read_factsheet),
        )
        if part is not None:
            factsheet_parts.append(part)
    # Diagonally, unlike the daily reports: the factsheet layout gains and
    # loses columns between months, and a strict concat would refuse a year
    # that spans one of those changes.
    factsheet = (
        pl.concat([pl.read_parquet(part) for part in factsheet_parts], how="diagonal")
        if factsheet_parts
        else pl.DataFrame(schema={"cnpj_classe": pl.String, "data": pl.Date})
    )

    cdi = readers.read_cdi(fetch("cdi", start=start, end=end, year=end.year))

    manifest.write(entries, cache_dir / "manifest.json")
    return Inputs(
        daily=daily,
        registry=registry,
        statement=statement,
        factsheet=factsheet,
        cdi=cdi,
        manifest={name: entry.sha256 for name, entry in entries.items()},
    )


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


def run(
    reference_date: dt.date,
    config_dir: Path = Path("configs"),
    output_dir: Path = Path("saida"),
    input_dir: Path | None = None,
    offline: bool = False,
    lookback_months: int | None = None,
    cache_dir: Path = Path("dados/raw"),
    simulations: int | None = None,
) -> RunResult:
    """Produce the ranking for one reference date."""
    universe_config = config.load_universe(config_dir / "universe.yaml")
    profiles_config = config.load_profiles(config_dir / "profiles.yaml")
    sources = config.load_sources(config_dir / "sources.yaml")
    transfer = config.load_transfer_settings(config_dir / "sources.yaml")

    months = lookback_months or universe_config.lookback_months
    start = _window_start(reference_date, months)

    inputs = (
        _load_offline(input_dir or Path("tests/fixtures"))
        if offline
        else _download(sources, transfer, start, reference_date, cache_dir)
    )

    # 1. Validate, and stop rather than rank a file that arrived broken.
    validated = schemas.validate_daily_report(inputs.daily, reference_date=reference_date)
    quality.assert_quarantine_within_limit(
        validated.received,
        len(validated.quarantined),
        universe_config.data_quality.max_quarantined_share,
    )
    schemas.assert_matches_contract(validated.clean)
    series = validated.clean.filter(pl.col("data") >= start)

    # 2. Who competes, counted at every step.
    terms = readers.combine_terms(
        readers.statement_in_force(inputs.statement, reference_date),
        readers.statement_in_force(inputs.factsheet, reference_date)
        if "data" in inputs.factsheet.columns
        else inputs.factsheet,
    )
    # The observation floor is declared for a twelve-month window; a shorter
    # window has proportionally fewer business days, and demanding 200 of 64
    # would empty the universe rather than filter it.
    filters = universe_config.filters.model_copy(
        update={"min_observations": round(universe_config.filters.min_observations * months / 12)}
    )
    built = universe.build(
        inputs.registry, series, terms, filters=filters, reference_date=reference_date
    )
    funnel = quality.compare_funnel(
        built.counts,
        universe_config.expected_funnel.steps,
        universe_config.expected_funnel.tolerance,
    )

    # 3. The benchmark, over exactly the window the funds are measured on.
    window = panel.benchmark_window(inputs.cdi, start, reference_date)
    benchmark = metrics.compound(window["taxa"].to_list())

    eligible_series = series.join(built.funds.select("cnpj_classe"), on="cnpj_classe", how="semi")
    measured = panel.build(eligible_series, benchmark_rate=benchmark, reference_date=reference_date)
    funds = built.funds.join(measured, on="cnpj_classe", how="inner").with_columns(
        pl.col("patrimonio_medio").log1p().alias("size"),
        pl.col("taxa_adm").alias("admin_fee"),
        pl.col("dias_resgate").alias("redemption_days"),
        pl.col("excesso").alias("excess_return"),
        pl.col("retorno_por_risco").alias("return_per_risk"),
        pl.col("volatilidade").alias("volatility"),
        pl.col("pior_queda").alias("max_drawdown"),
        pl.col("dias_negativos").alias("negative_days"),
        pl.col("estabilidade_fluxo").alias("flow_stability"),
    )

    # Resample the histories once and share the draws across profiles: the
    # underlying series is the same, and re-drawing per profile would only
    # invent a second version of the same uncertainty.
    order = funds["cnpj_classe"].to_list()
    draws = robustness.resample_metrics(
        eligible_series,
        order=order,
        benchmark=window,
        simulations=simulations or profiles_config.robustness.simulations,
        block_size=profiles_config.robustness.block_size_days,
        seed=profiles_config.robustness.seed,
    )
    slot_of = {cnpj: index for index, cnpj in enumerate(order)}

    rankings: list[schemas.ProfileRanking] = []
    eligible_by_profile: dict[str, list[str]] = {}
    for profile_id, profile in profiles_config.profiles.items():
        ranking, eligible = _rank_profile(
            funds,
            profile_id,
            profile,
            profiles_config,
            universe_config,
            simulations,
            draws,
            slot_of,
            eligible_series,
        )
        rankings.append(ranking)
        eligible_by_profile[profile_id] = eligible

    payload = schemas.RankingOutput(
        schema_version=writers.SCHEMA_VERSION,
        reference_date=reference_date,
        lookback_months=months,
        window_start=start,
        sources=inputs.manifest,
        profiles=rankings,
        benchmark_label="CDI",
        # Stated per peer group rather than once, because the field is what a
        # downstream consumer reads to know what a fund's excess return is
        # measured against. Every group names CDI here, and naming it group by
        # group is what makes that a published fact instead of an assumption
        # the reader has to make.
        benchmark_by_group=dict.fromkeys(
            sorted(str(name) for name in funds["classificacao_anbima"].unique() if name), "CDI"
        ),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    writers.write_json(payload, output_dir / "ranking.json")
    writers.write_markdown(payload, output_dir / "ranking.md", notes=_NOTES)
    (output_dir / "relatorio_qualidade.md").write_text(funnel.to_markdown(), encoding="utf-8")
    # Regenerated on every run so the page can never be older than the numbers
    # beside it. The verdict is carried over from the last out-of-sample test
    # if one has been run into this directory.
    html.write_html(payload, output_dir / "ranking.html", validation=_last_verdict(output_dir))

    return RunResult(
        payload=payload,
        funnel=funnel,
        max_observation_date=_latest_date(series, reference_date),
        output_dir=output_dir,
        quarantined_share=validated.quarantined_share,
        eligible_by_profile=eligible_by_profile,
        series=eligible_series,
        all_series=series.select("cnpj_classe", "data", "valor_cota"),
        benchmark_daily=window,
        fees={
            str(cnpj): float(fee)
            for cnpj, fee in zip(funds["cnpj_classe"], funds["taxa_adm"], strict=True)
            if fee is not None
        },
    )


def _duplicate_map(
    series: pl.DataFrame,
    funds: pl.DataFrame,
    max_tracking_difference: float,
    min_overlap_days: int,
) -> dict[str, dict[str, float]]:
    """Which funds are the same portfolio under another name.

    Returns, per fund, the funds it duplicates and how far apart they are. Two
    funds qualify when the same manager runs both and the annualised volatility
    of the difference between their daily returns falls below the threshold.
    The reasoning behind that pair of conditions is in `rank/selection.py`.

    Every pair is measured on the days both funds actually published a quota
    and on no others. Aligning the whole panel to its shortest member instead
    would hand every comparison the same handful of days, and any two series
    agree over a handful of days. The variance of the difference is obtained
    through a presence mask in three matrix products rather than one pass per
    pair, which matters because the simulation applies this same rule a
    thousand times and must not recompute it.
    """
    manager_of = dict(zip(funds["cnpj_classe"].to_list(), funds["gestor"].to_list(), strict=True))
    panel = (
        series.filter(pl.col("cnpj_classe").is_in(set(manager_of)))
        .sort("data")
        .pivot(on="cnpj_classe", index="data", values="valor_cota", aggregate_function="last")
    )
    columns = [name for name in panel.columns if name != "data"]
    if len(columns) < 2:
        return {}

    quotas = panel.select(columns).to_numpy().astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        values = quotas[1:] / quotas[:-1] - 1.0
    present = np.isfinite(values)
    values = np.where(present, values, 0.0)
    mask = present.astype(float)

    counts = mask.T @ mask
    sums = values.T @ mask
    squares = (values**2).T @ mask
    products = values.T @ values

    with np.errstate(divide="ignore", invalid="ignore"):
        # var(a - b) over the days the pair shares, annualised.
        mean_square = (squares + squares.T - 2 * products) / counts
        mean_gap = (sums - sums.T) / counts
        distance = np.sqrt(np.maximum(mean_square - mean_gap**2, 0.0)) * np.sqrt(
            BUSINESS_DAYS_PER_YEAR
        )
    distance = np.nan_to_num(distance, nan=np.inf, posinf=np.inf)
    distance[counts < min_overlap_days] = np.inf
    np.fill_diagonal(distance, np.inf)

    twins: dict[str, dict[str, float]] = {}
    for position, cnpj in enumerate(columns):
        manager = manager_of.get(cnpj)
        if manager is None:
            continue
        matched = np.flatnonzero(distance[position] <= max_tracking_difference)
        pairs = {
            columns[other]: float(distance[position, other])
            for other in matched
            if manager_of.get(columns[other]) == manager
        }
        if pairs:
            twins[cnpj] = pairs
    return twins


def _tax_regime(name: str | None, peer_group: str | None, long_term: str | None) -> str:
    """How the client is taxed on this fund, as far as public data can say.

    Debentures issued under the infrastructure incentive are exempt from income
    tax for individuals, so a fund built on them is not comparable, after tax,
    to a fund that follows the ordinary regressive table, even though the two
    sit in the same ANBIMA category and the delivery reports both before tax.
    Naming the regime per fund is what keeps that difference visible instead of
    being absorbed into a sentence about relative order holding.
    """
    haystack = f"{name or ''} {peer_group or ''}".upper()
    if "INCENTIVAD" in haystack or "INFRA" in haystack:
        return "isento_pf_incentivado"
    return "tabela_regressiva_longo_prazo" if long_term == "S" else "tabela_regressiva"


def _latest_date(series: pl.DataFrame, fallback: dt.date) -> dt.date:
    """The last day actually used, for the point-in-time assertion at the top."""
    if series.is_empty():
        return fallback
    latest = series["data"].max()
    return latest if isinstance(latest, dt.date) else fallback


def _last_verdict(output_dir: Path) -> str | None:
    """The one-line verdict from `validacao.md`, if the backtest has been run.

    Read rather than recomputed: the out-of-sample test takes a minute and
    rebuilds the ranking three times, which is not something an ordinary run
    should be made to do.
    """
    report = output_dir / "validacao.md"
    if not report.exists():
        return None
    for line in report.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Veredito:"):
            return line.removeprefix("## Veredito:").strip()
    return None


def _window_start(reference_date: dt.date, months: int) -> dt.date:
    """The first day of a window that is exactly `months` long.

    The window is closed at both ends and counted back from the reference date
    itself, not from the start of its month: twelve months ending on
    31/12/2025 begin on 01/01/2025 and hold about 249 business days.

    Counting back to the first day of the month twelve months earlier would
    begin on 01/12/2024 and hand thirteen months of quotas to something
    labelled twelve. The reader could not reconcile that return against
    anything the fund publishes, and the benchmark would sit a full percentage
    point away from the CDI of the calendar year.
    """
    year = reference_date.year - (months // 12)
    month = reference_date.month - (months % 12)
    if month <= 0:
        year, month = year - 1, month + 12
    day = min(reference_date.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day) + dt.timedelta(days=1)


def _rank_profile(
    funds: pl.DataFrame,
    profile_id: str,
    profile: config.Profile,
    profiles_config: config.ProfilesConfig,
    universe_config: config.UniverseConfig,
    simulations: int | None = None,
    draws: dict[str, np.ndarray] | None = None,
    slot_of: dict[str, int] | None = None,
    pool_series: pl.DataFrame | None = None,
) -> tuple[schemas.ProfileRanking, list[str]]:
    """Eligibility first, then percentiles, and never the other way round."""
    pool = eligibility.for_profile(funds, profile.eligibility)
    top_n = profiles_config.robustness.top_n
    eligible = pool["cnpj_classe"].to_list() if not pool.is_empty() else []
    if pool.is_empty():
        return (
            schemas.ProfileRanking(
                profile_id=profile_id,
                label=profile.label,
                eligible_universe_size=0,
                weights=profile.weights,
                effective_weights=profile.weights,
                top=[],
                top_n=top_n,
            ),
            eligible,
        )

    # Weight only what can still discriminate. A criterion already enforced as
    # a filter arrives here with every fund tied on it, and a weight spent on a
    # tie is a weight subtracted from the metrics that could separate.
    weights, inert = scoring.effective_weights(
        pool, profile.weights, profiles_config.scoring.min_dispersion
    )

    grouped = scoring.merge_small_groups(
        pool, group="classificacao_anbima", min_size=universe_config.peer_groups.min_size
    )
    directions = {name: spec.direction for name, spec in profiles_config.metrics.items()}
    clip = profiles_config.scoring.winsorise
    scored = grouped
    for name in weights:
        if name in scored.columns:
            scored = scoring.winsorise(scored, metric=name, lower=clip.lower, upper=clip.upper)
            scored = scoring.peer_percentile(
                scored, metric=name, group="peer_group_effective", direction=directions[name]
            )
    scored = scoring.total_score(scored, weights)

    # The same score against the whole eligible pool. The peer score decides
    # the ranking; this one says what being first of eighteen is worth, which a
    # percentile inside a category cannot tell you on its own.
    pool_scored = grouped.with_columns(
        pl.lit(scoring.GLOBAL_PEER_GROUP).alias("peer_group_effective")
    )
    for name in weights:
        if name in pool_scored.columns:
            pool_scored = scoring.winsorise(
                pool_scored, metric=name, lower=clip.lower, upper=clip.upper
            )
            pool_scored = scoring.peer_percentile(
                pool_scored, metric=name, group="peer_group_effective", direction=directions[name]
            )
    pool_scored = scoring.total_score(pool_scored, weights)
    score_pool = dict(
        zip(pool_scored["cnpj_classe"].to_list(), pool_scored["score"].to_list(), strict=True)
    )

    duplicates = _duplicate_map(
        pool_series if pool_series is not None else pl.DataFrame(),
        pool,
        profiles_config.selection.max_tracking_difference,
        profiles_config.selection.min_overlap_days,
    )
    identifiers = scored["cnpj_classe"].to_list()

    # The draws were computed over the full eligible set, so they are cut down
    # to this profile's funds, in this frame's row order.
    profile_draws = None
    if draws and slot_of:
        columns = [slot_of[cnpj] for cnpj in identifiers]
        profile_draws = {name: array[:, columns] for name, array in draws.items()}

    stability = robustness.simulate(
        scored,
        weights=weights,
        jitter=profile.jitter,
        # The metrics that move between simulations are the ones derived from
        # the return series. Naming them lets the report separate real
        # robustness from the mechanical kind that a constant fee provides.
        varying_metrics=list(profile_draws) if profile_draws else None,
        metric_draws=profile_draws,
        metrics_config={name: directions[name] for name in weights},
        group="peer_group_effective",
        seed=profiles_config.robustness.seed,
        simulations=simulations or profiles_config.robustness.simulations,
        top_n=top_n,
        duplicates={name: frozenset(pairs) for name, pairs in duplicates.items()},
    )
    scored = scored.join(stability, on="cnpj_classe", how="left")

    # Published in order of how often a fund survived, not of where it landed
    # once, and then trimmed to five funds rather than five scores: two share
    # classes of one portfolio are two rows here and one exposure in a client's
    # account. See decisions D-011 and D-040.
    ordered = scored.sort(["appearance_rate", "score"], descending=True)
    chosen, displaced = selection.pick_distinct(
        ordered["cnpj_classe"].to_list(), duplicates, top_n=top_n
    )
    names = dict(
        zip(ordered["cnpj_classe"].to_list(), ordered["denominacao_social"].to_list(), strict=True)
    )
    scores = dict(zip(ordered["cnpj_classe"].to_list(), ordered["score"].to_list(), strict=True))
    best = ordered.filter(pl.col("cnpj_classe").is_in(chosen)).sort(
        pl.col("cnpj_classe").replace_strict({c: i for i, c in enumerate(chosen)}, default=99)
    )

    ranked: list[schemas.RankedFund] = []
    for position, row in enumerate(best.iter_rows(named=True), start=1):
        fund = schemas.RankedFund(
            rank=position,
            cnpj_classe=row["cnpj_classe"],
            name=row.get("denominacao_social") or row["cnpj_classe"],
            manager=row.get("gestor"),
            peer_group=row.get("peer_group_effective"),
            score=float(row["score"]),
            score_pool=float(score_pool.get(row["cnpj_classe"], row["score"])),
            appearance_rate=float(row.get("appearance_rate") or 0.0),
            appearance_rate_variable_only=(
                float(row["appearance_rate_variable_only"])
                if row.get("appearance_rate_variable_only") is not None
                else None
            ),
            metrics={
                key: row.get(key)
                for key in (
                    "retorno",
                    "excesso",
                    "volatilidade",
                    "retorno_por_risco",
                    "pior_queda",
                    "dias_negativos",
                    "taxa_adm",
                    "dias_resgate",
                    "patrimonio_medio",
                    "cotistas",
                    "observacoes",
                    "fonte_taxa",
                    "taxa_zero_declarada",
                )
            }
            | {
                "regime_tributario": _tax_regime(
                    row.get("denominacao_social"),
                    row.get("classificacao_anbima"),
                    row.get("tributacao_longo_prazo"),
                )
            },
            percentiles={
                name: float(row[f"{name}_pct"])
                for name in weights
                if f"{name}_pct" in row and row[f"{name}_pct"] is not None
            },
        )
        fund.rationale = writers.describe(fund)
        ranked.append(fund)

    return (
        schemas.ProfileRanking(
            profile_id=profile_id,
            label=profile.label,
            eligible_universe_size=len(pool),
            weights=profile.weights,
            effective_weights=weights,
            inert_metrics=inert,
            displaced=[
                schemas.Displaced(
                    cnpj_classe=item.cnpj_classe,
                    name=names.get(item.cnpj_classe) or item.cnpj_classe,
                    score=float(scores.get(item.cnpj_classe) or 0.0),
                    duplicate_of=names.get(item.duplicate_of) or item.duplicate_of,
                    tracking_difference=item.tracking_difference,
                )
                for item in displaced
            ],
            manager_share=_manager_share(pool),
            top=ranked,
            top_n=top_n,
        ),
        eligible,
    )


def _manager_share(pool: pl.DataFrame) -> dict[str, float]:
    """How concentrated the pool a profile chose from already is.

    A list drawn from a universe where one house runs a quarter of the funds
    will name that house repeatedly, and without this number the reader cannot
    tell a ranking that concentrated from a universe that already was. Only the
    largest few are reported; the tail says nothing.
    """
    if pool.is_empty() or "gestor" not in pool.columns:
        return {}
    counted = pool.group_by("gestor").len().sort("len", descending=True).head(5)
    return {
        str(name): round(int(size) / len(pool), 4)
        for name, size in zip(counted["gestor"], counted["len"], strict=True)
        if name is not None
    }


_NOTES = [
    # Deliberately does not repeat the two headline limitations, nor the note
    # about constant fees inflating apparent stability. The first two are
    # stated in full above, and the third is answered with a number by the
    # "só pelo desempenho" column. A caveat restated twice reads as
    # carelessness, and it teaches the reader to skim the ones that appear
    # only once.
    "**Só entra fundo que publica taxa e prazo de resgate.** Não se recomenda o que não se "
    "consegue precificar. Isso exclui 26% dos fundos que passariam nos demais filtros, e a "
    "exclusão não é aleatória: a obrigação de publicar lâmina alcança fundos de varejo e não "
    "os restritos a investidor qualificado.",
    "**Todos os fundos são medidos contra o CDI**, inclusive os indexados à inflação. A "
    "ANBIMA publica o IMA como foto do dia, e não como série histórica, então uma janela que "
    "termina numa data passada não se reconstrói a partir dele. Como a comparação é feita "
    "dentro do grupo de pares, um benchmark deslocado move todo o grupo junto e não altera a "
    "ordem por excesso. O que ele altera é o retorno por unidade de risco, que divide esse "
    "excesso por volatilidades diferentes. Afeta 8% do universo e uma das duas métricas de "
    "desempenho.",
    "**O imposto de renda fica de fora, e isso não é neutro para todo mundo.** A maioria dos "
    "fundos segue a mesma tabela regressiva, e entre eles a ordem relativa se mantém. Fundos "
    "incentivados de infraestrutura são **isentos para pessoa física**, então o que o "
    "cliente leva para casa é maior do que a tabela mostra, e a comparação bruta os "
    "subestima. O regime de cada fundo está no `ranking.json`, no campo `regime_tributario`.",
    "**Fundos que fecharam não estão na base.** O universo é, por construção, otimista: quem "
    "quebrou em 2025 não aparece para ser comparado.",
    "**A oscilação dos fundos de crédito é subestimada.** Dívida privada no Brasil não é "
    "remarcada todo dia como uma ação, o que faz esses fundos parecerem mais tranquilos do "
    "que são e melhora artificialmente a nota de quem carrega mais risco.",
    "**A taxa é contada duas vezes, de propósito.** A cota do informe diário já vem "
    "líquida, então o retorno em excesso ali dentro já pune o fundo caro. Dar à taxa o maior "
    "peso conta o mesmo custo de novo. A segunda contagem é a que fala sobre 2026, enquanto "
    "a primeira fala sobre 2025. É escolha, e não descuido.",
    "**Cada fundo é avaliado sozinho**, não como parte de uma carteira. Não há restrição de "
    "diversificação além de não repetir a mesma carteira duas vezes, então os cinco escolhidos "
    "podem ser parecidos entre si sem serem idênticos.",
]
