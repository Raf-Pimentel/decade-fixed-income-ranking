"""The whole thing, in one importable function.

`run(reference_date=...)` is the entire programme. The command line is a thin
wrapper over it, and another team can import it directly — which is the point
of the exercise: the ranking has to be consumable without anyone explaining it
first.

Point-in-time is enforced at three separate places: when the daily report is
validated, when the statement in force is chosen, and again when the panel is
built. That looks like belt and braces because it is. A single row from after
the reference date would not raise anything — it would just make the backtest
in phase 5.5 quietly optimistic, which is the one failure this project cannot
afford.
"""

from __future__ import annotations

import datetime as dt
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl

from ranking import config
from ranking.contracts import quality, schemas
from ranking.extract import http, manifest, readers
from ranking.publish import writers
from ranking.rank import eligibility, robustness, scoring
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

    daily_frames = []
    for year, month in months:
        archive = fetch("daily_report", year=year, month=month)
        member = _extract(archive, f"inf_diario_fi_{year}{month:02d}.csv", unpacked)
        if member is not None:
            daily_frames.append(readers.read_daily_report(member))
    daily = pl.concat(daily_frames)

    registry_zip = fetch("registry")
    classes = _extract(registry_zip, "registro_classe.csv", unpacked)
    funds_file = _extract(registry_zip, "registro_fundo.csv", unpacked)
    if classes is None or funds_file is None:
        raise RuntimeError("the CVM registry archive is missing its expected members")
    registry = readers.read_registry(classes, funds_file)

    statement = readers.read_statement(fetch("statement", year=end.year))

    factsheets = []
    for year, month in months:
        archive = fetch("factsheet", year=year, month=month)
        member = _extract(archive, f"lamina_fi_{year}{month:02d}.csv", unpacked)
        if member is not None:
            factsheets.append(readers.read_factsheet(member))
    factsheet = (
        pl.concat(factsheets, how="diagonal")
        if factsheets
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
        benchmark_rate=benchmark,
        simulations=simulations or profiles_config.robustness.simulations,
        block_size=profiles_config.robustness.block_size_days,
        seed=profiles_config.robustness.seed,
    )
    slot_of = {cnpj: index for index, cnpj in enumerate(order)}

    rankings = [
        _rank_profile(
            funds,
            profile_id,
            profile,
            profiles_config,
            universe_config,
            simulations,
            draws,
            slot_of,
        )
        for profile_id, profile in profiles_config.profiles.items()
    ]

    payload = schemas.RankingOutput(
        schema_version=writers.SCHEMA_VERSION,
        reference_date=reference_date,
        lookback_months=months,
        sources=inputs.manifest,
        profiles=rankings,
        benchmark_label="CDI",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    writers.write_json(payload, output_dir / "ranking.json")
    writers.write_markdown(payload, output_dir / "ranking.md", notes=_NOTES)
    (output_dir / "relatorio_qualidade.md").write_text(funnel.to_markdown(), encoding="utf-8")

    return RunResult(
        payload=payload,
        funnel=funnel,
        max_observation_date=_latest_date(series, reference_date),
        output_dir=output_dir,
        quarantined_share=validated.quarantined_share,
    )


def _latest_date(series: pl.DataFrame, fallback: dt.date) -> dt.date:
    """The last day actually used, for the point-in-time assertion at the top."""
    if series.is_empty():
        return fallback
    latest = series["data"].max()
    return latest if isinstance(latest, dt.date) else fallback


def _window_start(reference_date: dt.date, months: int) -> dt.date:
    year = reference_date.year - (months // 12)
    month = reference_date.month - (months % 12)
    if month <= 0:
        year, month = year - 1, month + 12
    return dt.date(year, month, 1)


def _rank_profile(
    funds: pl.DataFrame,
    profile_id: str,
    profile: config.Profile,
    profiles_config: config.ProfilesConfig,
    universe_config: config.UniverseConfig,
    simulations: int | None = None,
    draws: dict[str, np.ndarray] | None = None,
    slot_of: dict[str, int] | None = None,
) -> schemas.ProfileRanking:
    """Eligibility first, then percentiles — never the other way round."""
    pool = eligibility.for_profile(funds, profile.eligibility)
    top_n = profiles_config.robustness.top_n
    if pool.is_empty():
        return schemas.ProfileRanking(
            profile_id=profile_id,
            label=profile.label,
            eligible_universe_size=0,
            weights=profile.weights,
            top=[],
            top_n=top_n,
        )

    grouped = scoring.merge_small_groups(
        pool, group="classificacao_anbima", min_size=universe_config.peer_groups.min_size
    )
    directions = {name: spec.direction for name, spec in profiles_config.metrics.items()}
    scored = grouped
    for name in profile.weights:
        if name in scored.columns:
            scored = scoring.winsorise(scored, metric=name, lower=0.01, upper=0.99)
            scored = scoring.peer_percentile(
                scored, metric=name, group="peer_group_effective", direction=directions[name]
            )
    scored = scoring.total_score(scored, profile.weights)

    # The draws were computed over the full eligible set, so they are cut down
    # to this profile's funds, in this frame's row order.
    profile_draws = None
    if draws and slot_of:
        columns = [slot_of[cnpj] for cnpj in scored["cnpj_classe"].to_list()]
        profile_draws = {name: array[:, columns] for name, array in draws.items()}

    stability = robustness.simulate(
        scored,
        weights=profile.weights,
        jitter=profile.jitter,
        metric_draws=profile_draws,
        metrics_config={name: directions[name] for name in profile.weights},
        group="peer_group_effective",
        seed=profiles_config.robustness.seed,
        simulations=simulations or profiles_config.robustness.simulations,
        top_n=top_n,
    )
    scored = scored.join(stability, on="cnpj_classe", how="left")

    # Published in order of how often a fund survived, not of where it landed
    # once. See decision D-011.
    best = scored.sort(["appearance_rate", "score"], descending=True).head(top_n)

    ranked: list[schemas.RankedFund] = []
    for position, row in enumerate(best.iter_rows(named=True), start=1):
        fund = schemas.RankedFund(
            rank=position,
            cnpj_classe=row["cnpj_classe"],
            name=row.get("denominacao_social") or row["cnpj_classe"],
            manager=row.get("gestor"),
            peer_group=row.get("peer_group_effective"),
            score=float(row["score"]),
            appearance_rate=float(row.get("appearance_rate") or 0.0),
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
            },
            percentiles={
                name: float(row[f"{name}_pct"])
                for name in profile.weights
                if f"{name}_pct" in row and row[f"{name}_pct"] is not None
            },
        )
        fund.rationale = writers.describe(fund)
        ranked.append(fund)

    return schemas.ProfileRanking(
        profile_id=profile_id,
        label=profile.label,
        eligible_universe_size=len(pool),
        weights=profile.weights,
        top=ranked,
        top_n=top_n,
    )


_NOTES = [
    "**Não olhamos a carteira.** O ranking mede resultado, não conteúdo. Dois fundos com "
    "números idênticos podem carregar riscos de crédito completamente diferentes.",
    "**A ordem entre os cinco não é significativa.** A taxa de aparição mede isso.",
    "**Taxas e prazos não variam na simulação**, então parte da estabilidade é mecânica.",
    "**Fundos indexados à inflação são medidos contra o CDI**, não contra o IMA-B — "
    "a série histórica do IMA não é publicada em formato utilizável.",
    "**O universo só sobreviveu quem publica taxa e prazo.** Não se recomenda o que não "
    "se consegue precificar.",
]
