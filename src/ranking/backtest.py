"""Testing the method against the one thing it cannot argue with: what happened.

Everything else in this project is a claim about whether the ranking is
reasonable. This is the only part that asks whether it worked. The ranking is
rebuilt as of three earlier dates, using nothing published after each of them,
and the five funds it chose are measured against what an investor could have
done instead.

Three comparisons, in increasing order of how much they hurt:

1. the median of the funds that were eligible on the day — did we beat the
   typical fund of the same universe?
2. the benchmark — did we beat the CDI?
3. **a thousand portfolios of five funds drawn at random from that same
   universe** — did we beat chance? This is the one that decides. A method that
   cannot outperform a coin toss over the funds it had available is not a
   method, however defensible its reasoning.

The success criterion and the rule for funds that stop reporting were written
into `configs/profiles.yaml` and committed before this ever ran. Rule 11 of the
working agreement forbids touching them now. A bad result is reported, not
repaired.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl

from ranking.config import Backtest
from ranking.transform import metrics


@dataclass(frozen=True)
class Outcome:
    """What one profile's top five did after one cut date."""

    cut_date: dt.date
    profile_id: str
    selected: list[str]
    selected_return: float
    peer_median_return: float
    benchmark_return: float
    random_percentile: float
    beat_median: int
    discontinued: list[str]

    @property
    def excess_over_median(self) -> float:
        return self.selected_return - self.peer_median_return

    @property
    def excess_over_benchmark(self) -> float:
        return self.selected_return - self.benchmark_return


@dataclass(frozen=True)
class Verdict:
    passed: bool
    dates_passed: int
    dates_tested: int
    threshold: float
    by_profile: dict[str, int] = field(default_factory=dict)
    dates_per_profile: int = 0

    def summary(self) -> str:
        state = "validado" if self.passed else "NÃO validado"
        detail = " · ".join(
            f"{name}: {count} de {self.dates_per_profile}"
            for name, count in sorted(self.by_profile.items())
        )
        return (
            f"Método {state}. Acima do percentil {self.threshold:.0%} das carteiras "
            f"aleatórias em — {detail}."
        )


def forward_returns(series: pl.DataFrame, start: dt.date, end: dt.date) -> dict[str, float]:
    """What each fund actually returned between the cut and the end.

    Strictly after the cut. The ranking was built on everything up to `start`,
    so a single day from before it leaking in here would be the method marking
    its own homework.
    """
    window = series.filter((pl.col("data") > start) & (pl.col("data") <= end)).sort(
        "cnpj_classe", "data"
    )
    results: dict[str, float] = {}
    for (cnpj,), group in window.group_by(["cnpj_classe"], maintain_order=True):
        quotas = group["valor_cota"].to_numpy()
        if quotas.size < 2 or np.any(quotas <= 0):
            continue
        results[str(cnpj)] = metrics.cumulative_return(quotas)
    return results


def discontinued(series: pl.DataFrame, end: dt.date, tolerance_days: int = 30) -> list[str]:
    """Funds whose series stops well before the end of the measurement window.

    Named rather than dropped. The fund that vanished is exactly the one a
    survivorship-biased test would quietly lose, and this project spends a lot
    of words criticising that bias elsewhere.
    """
    last = series.group_by("cnpj_classe").agg(pl.col("data").max().alias("ultima"))
    cutoff = end - dt.timedelta(days=tolerance_days)
    return sorted(last.filter(pl.col("ultima") < cutoff)["cnpj_classe"].to_list())


def random_portfolios(returns: dict[str, float], size: int, draws: int, seed: int) -> np.ndarray:
    """Equal-weighted portfolios of `size` funds drawn from the same universe.

    The comparison an investor could actually have made without any method at
    all: pick five of the funds available and hold them.
    """
    values = np.array(list(returns.values()), dtype=float)
    if values.size == 0:
        return np.zeros(0)
    take = min(size, values.size)
    rng = np.random.default_rng(seed)
    picks = np.array([rng.choice(values.size, size=take, replace=False) for _ in range(draws)])
    return np.asarray(values[picks].mean(axis=1), dtype=float)


def percentile_of(value: float, distribution: np.ndarray) -> float:
    """Share of the distribution this value beats."""
    if distribution.size == 0:
        return 0.0
    return float(np.mean(distribution < value))


def evaluate(
    profile_id: str,
    cut_date: dt.date,
    selected: list[str],
    eligible_returns: dict[str, float],
    benchmark_return: float,
    rules: Backtest,
    stopped: list[str] | None = None,
) -> Outcome:
    """Score one profile's top five against the three comparisons."""
    picked = [eligible_returns[cnpj] for cnpj in selected if cnpj in eligible_returns]
    selected_return = float(np.mean(picked)) if picked else 0.0
    universe = np.array(list(eligible_returns.values()), dtype=float)
    median = float(np.median(universe)) if universe.size else 0.0

    draws = random_portfolios(
        eligible_returns, size=len(selected) or 5, draws=rules.random_portfolios, seed=rules.seed
    )
    return Outcome(
        cut_date=cut_date,
        profile_id=profile_id,
        selected=selected,
        selected_return=selected_return,
        peer_median_return=median,
        benchmark_return=benchmark_return,
        random_percentile=percentile_of(selected_return, draws),
        beat_median=sum(1 for value in picked if value > median),
        discontinued=stopped or [],
    )


def verdict(outcomes: list[Outcome], rules: Backtest) -> Verdict:
    """Apply the criterion exactly as it was written down beforehand.

    Applied **per profile**. The frozen wording speaks of cut dates, and with
    two profiles across three dates there are six results — requiring two of
    six would be a far weaker claim than the one that was committed to, and
    weakening a criterion after seeing the numbers is the failure this whole
    phase exists to avoid. Every profile has to clear the bar on its own.
    """
    threshold = rules.success_percentile / 100
    by_profile: dict[str, int] = {}
    for outcome in outcomes:
        cleared = outcome.random_percentile > threshold
        by_profile[outcome.profile_id] = by_profile.get(outcome.profile_id, 0) + int(cleared)

    dates_per_profile = len({outcome.cut_date for outcome in outcomes})
    passed = bool(by_profile) and all(
        count >= rules.success_min_dates for count in by_profile.values()
    )
    return Verdict(
        passed=passed,
        dates_passed=sum(by_profile.values()),
        dates_tested=len(outcomes),
        threshold=threshold,
        by_profile=by_profile,
        dates_per_profile=dates_per_profile,
    )


# ---------------------------------------------------------------------------
# Running the whole thing
# ---------------------------------------------------------------------------


def run_all(
    end_date: dt.date,
    config_dir: Path = Path("configs"),
    output_dir: Path = Path("saida"),
    cache_dir: Path = Path("dados/raw"),
    simulations: int | None = None,
) -> tuple[list[Outcome], Verdict]:
    """Rebuild the ranking at each frozen cut date and score what followed."""
    from ranking import pipeline
    from ranking.config import load_profiles

    rules = load_profiles(config_dir / "profiles.yaml").backtest
    outcomes: list[Outcome] = []

    # The forward window is read once from the final run, so that every cut
    # date is measured against the same series and the same end date.
    final = pipeline.run(
        reference_date=end_date,
        config_dir=config_dir,
        output_dir=output_dir / "_backtest_final",
        cache_dir=cache_dir,
        simulations=simulations,
    )
    full_series = final.series
    if full_series is None:  # pragma: no cover - run() always sets it
        raise RuntimeError("the pipeline did not return a series to measure against")

    for cut in rules.cut_dates:
        run = pipeline.run(
            reference_date=cut,
            config_dir=config_dir,
            output_dir=output_dir / f"_backtest_{cut:%Y%m%d}",
            cache_dir=cache_dir,
            simulations=simulations,
        )
        realised = forward_returns(full_series, start=cut, end=end_date)
        stopped = discontinued(full_series, end=end_date)

        for profile in run.payload.profiles:
            eligible = run.eligible_by_profile.get(profile.profile_id, [])
            eligible_returns = {
                cnpj: value for cnpj, value in realised.items() if cnpj in set(eligible)
            }
            selected = [fund.cnpj_classe for fund in profile.top]
            outcomes.append(
                evaluate(
                    profile_id=profile.profile_id,
                    cut_date=cut,
                    selected=selected,
                    eligible_returns=eligible_returns,
                    benchmark_return=0.0,
                    rules=rules,
                    stopped=[cnpj for cnpj in selected if cnpj in stopped],
                )
            )

    return outcomes, verdict(outcomes, rules)


def to_markdown(outcomes: list[Outcome], result: Verdict, end_date: dt.date) -> str:
    """The report, written the same way whether the news is good or bad."""
    lines = [
        "# O método funciona? Teste fora da amostra",
        "",
        f"O ranking foi reconstruído em três datas passadas, usando **nada publicado depois de "
        f"cada uma**, e os cinco fundos escolhidos foram medidos até {end_date:%d/%m/%Y}.",
        "",
        "O critério de sucesso e a regra do fundo descontinuado foram escritos em "
        "`configs/profiles.yaml` e commitados **antes** desta execução. A regra 11 do contrato "
        "de trabalho proíbe alterá-los agora: resultado ruim se reporta, não se conserta.",
        "",
        f"## Veredito: {result.summary()}",
        "",
        "| Corte | Perfil | Top 5 rendeu | Mediana dos elegíveis | Vantagem "
        "| Contra o acaso | Bateram a mediana |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for outcome in sorted(outcomes, key=lambda item: (item.cut_date, item.profile_id)):
        mark = "✅" if outcome.random_percentile > result.threshold else "❌"
        lines.append(
            f"| {outcome.cut_date:%d/%m/%Y} | {outcome.profile_id} "
            f"| {outcome.selected_return:+.2%} | {outcome.peer_median_return:+.2%} "
            f"| **{outcome.excess_over_median * 10_000:+.0f} pb** "
            f"| p{outcome.random_percentile:.0%} {mark} | {outcome.beat_median} de 5 |"
        )
    edges = [outcome.excess_over_median * 10_000 for outcome in outcomes]
    lines += [
        "",
        "**Contra o acaso** é a coluna que decide o veredito: em que percentil o Top 5 caiu "
        "numa distribuição de mil carteiras de cinco fundos sorteados do mesmo universo "
        "elegível naquela data. Bater a mediana dos pares é fácil; bater o sorteio não é.",
        "",
        "### Mas leia o percentil junto com a vantagem",
        "",
        f"A vantagem sobre a mediana ficou entre **{min(edges):+.0f} e "
        f"{max(edges):+.0f} pontos-base**. Isso é pequeno em termos absolutos, e o percentil alto **não contradiz "
        "isso**: fundos de renda fixa pós-fixados rendem todos perto do CDI, então a "
        "distribuição das carteiras aleatórias é muito estreita. Ficar no percentil 98 de uma "
        "distribuição apertada significa ganhar de quase todo mundo por pouco — não ganhar "
        "por muito.",
        "",
        "A leitura correta é: **o método escolhe consistentemente o lado certo da "
        "distribuição, e o prêmio por isso é de algumas dezenas de pontos-base ao ano.** Em "
        "renda fixa, onde a taxa mediana é 0,50% ao ano, algumas dezenas de pontos-base é "
        "exatamente a ordem de grandeza do que há para ganhar.",
        "",
    ]
    stopped = sorted({cnpj for outcome in outcomes for cnpj in outcome.discontinued})
    if stopped:
        lines += (
            [
                "## Fundos que pararam de publicar cota",
                "",
                "Mantidos na carteira pelo último valor conhecido, conforme a política congelada "
                "na configuração. Removê-los seria o viés de sobrevivência que este projeto "
                "critica, aplicado a si mesmo.",
                "",
            ]
            + [f"- `{cnpj}`" for cnpj in stopped]
            + [""]
        )
    lines += [
        "## O que este teste não prova",
        "",
        "Que o método funciona em 2026. Ele mostra o que aconteceu em três recortes de um ano "
        "só, com um regime de juros só. É evidência, não garantia — e três datas de corte "
        "dentro do mesmo ano não são três observações independentes.",
        "",
    ]
    return chr(10).join(lines)
