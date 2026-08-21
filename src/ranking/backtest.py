"""Testing the method against the one thing it cannot argue with: what happened.

Everything else in this project is a claim about whether the ranking is
reasonable. This is the only part that asks whether it worked. The ranking is
rebuilt as of three earlier dates, using nothing published after each of them,
and the five funds it chose are measured against what an investor could have
done instead.

Four comparisons, in increasing order of how much they hurt:

1. the median of the funds that were eligible on the day — did we beat the
   typical fund of the same universe?
2. the benchmark — the CDI compounded over exactly the days being measured,
   so that the answer is a real number rather than a placeholder;
3. **a thousand portfolios of five funds drawn at random from that same
   universe** — did we beat chance? This is the one that decides the frozen
   criterion. A method that cannot outperform a coin toss over the funds it
   had available is not a method, however defensible its reasoning;
4. **a thousand portfolios drawn from the cheapest quarter of that universe.**
   Cost is deducted from the quota before anybody measures anything, so a
   ranking whose heaviest weight is the fee earns part of its advantage by
   arithmetic that was knowable before the test was written. Holding cost
   roughly constant separates that part from whatever else the method is
   doing. This one is reported, not part of the criterion, which was frozen
   before it existed.

What every fund is measured on is the full validated panel, not the funds that
were still eligible at the end. A fund chosen in March that shrank below the
shareholder floor by December still had a return, and reading outcomes from
the surviving universe would silently drop it from the average — survivorship
bias inside the very test written to avoid it.

The success criterion and the rule for funds that stop reporting were written
into `configs/profiles.yaml` and committed before this ever ran. Rule 11 of the
working agreement forbids touching them now. A bad result is reported, not
repaired.
"""

from __future__ import annotations

import datetime as dt
import shutil
import tempfile
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
    # The same comparison against portfolios drawn from the cheapest quarter of
    # the same universe. Cost is deducted from the quota, so a method that
    # prefers cheap funds earns part of its advantage by arithmetic rather than
    # by selection; this is the part that survives once that is held constant.
    cheap_percentile: float
    beat_median: int
    discontinued: list[str]
    # Selected funds with no quota published after the cut date at all. Held at
    # their last known value, per the frozen policy, and named here.
    carried: list[str]

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


def benchmark_return(daily: pl.DataFrame | None, start: dt.date, end: dt.date) -> float:
    """The CDI compounded over the same days the funds are measured on.

    Strictly after the cut and up to the end, matching `forward_returns`
    exactly. Compounding rather than summing: at Brazilian levels the
    difference over a year is worth several percentage points, which is far
    larger than anything this test is trying to detect.
    """
    if daily is None or daily.is_empty():
        return 0.0
    window = daily.filter((pl.col("data") > start) & (pl.col("data") <= end))
    return metrics.compound(window["taxa"].to_list())


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


def cheapest_quartile(returns: dict[str, float], fees: dict[str, float]) -> dict[str, float]:
    """The quarter of the universe that charges least, by admin fee.

    A ranking whose heaviest weight is cost will beat the median fund partly
    because cheap funds keep more of the same gross return — that is
    arithmetic, known before any test is run, and it would show up as apparent
    skill in a comparison against the whole universe. Drawing the control from
    funds that are already cheap holds that constant and leaves the question
    the test is actually for: among funds of similar cost, does the method pick
    better ones?
    """
    priced = {cnpj: fees[cnpj] for cnpj in returns if cnpj in fees}
    if len(priced) < 8:
        return dict(returns)
    cut = float(np.quantile(np.array(list(priced.values()), dtype=float), 0.25))
    return {cnpj: value for cnpj, value in returns.items() if priced.get(cnpj, cut + 1) <= cut}


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
    fees: dict[str, float] | None = None,
    forward_returns_all: dict[str, float] | None = None,
) -> Outcome:
    """Score one profile's top five against the comparisons.

    Every selected fund contributes, including one that has left the eligible
    universe since the cut date. Averaging over only the survivors would be the
    survivorship bias this test exists to avoid, applied to the test itself: a
    fund that shrank, closed to new money or stopped disclosing is exactly the
    outcome a method should be charged for. A fund with no quota published
    after the cut at all is held at its last known value — flat — which is the
    policy frozen in configuration before any of this ran.
    """
    outcomes = forward_returns_all or eligible_returns
    picked = [outcomes.get(cnpj, 0.0) for cnpj in selected]
    carried = [cnpj for cnpj in selected if cnpj not in outcomes]
    selected_return = float(np.mean(picked)) if picked else 0.0
    universe = np.array(list(eligible_returns.values()), dtype=float)
    median = float(np.median(universe)) if universe.size else 0.0

    size = len(selected) or 5
    draws = random_portfolios(
        eligible_returns, size=size, draws=rules.random_portfolios, seed=rules.seed
    )
    cheap = random_portfolios(
        cheapest_quartile(eligible_returns, fees or {}),
        size=size,
        draws=rules.random_portfolios,
        seed=rules.seed,
    )
    return Outcome(
        cut_date=cut_date,
        profile_id=profile_id,
        selected=selected,
        selected_return=selected_return,
        peer_median_return=median,
        benchmark_return=benchmark_return,
        random_percentile=percentile_of(selected_return, draws),
        cheap_percentile=percentile_of(selected_return, cheap),
        beat_median=sum(1 for value in picked if value > median),
        discontinued=stopped or [],
        carried=carried,
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
    # Each cut date rebuilds the whole ranking, which writes a full set of
    # outputs. Those go to a scratch directory rather than beside the real
    # deliverables: `saida/` should hold the answer, not the working out.
    scratch = Path(tempfile.mkdtemp(prefix="backtest-"))

    # The forward window is read once from the final run, so that every cut
    # date is measured against the same series and the same end date. It is the
    # whole validated panel — every fund that published a quota, eligible or
    # not — because the outcome of a fund that fell out of the universe is part
    # of the result, not something to be excused from it.
    final = pipeline.run(
        reference_date=end_date,
        config_dir=config_dir,
        output_dir=scratch / "final",
        cache_dir=cache_dir,
        simulations=simulations,
    )
    full_series = final.all_series
    if full_series is None:  # pragma: no cover - run() always sets it
        raise RuntimeError("the pipeline did not return a series to measure against")
    benchmark_daily = final.benchmark_daily
    # The final run has given up everything it is needed for. Releasing it here
    # matters: each cut date builds a panel of its own, and holding two of them
    # open is the peak of the whole programme.
    del final

    for cut in rules.cut_dates:
        run = pipeline.run(
            reference_date=cut,
            config_dir=config_dir,
            output_dir=scratch / f"{cut:%Y%m%d}",
            cache_dir=cache_dir,
            simulations=simulations,
        )
        realised = forward_returns(full_series, start=cut, end=end_date)
        stopped = discontinued(full_series, end=end_date)
        benchmark = benchmark_return(benchmark_daily, start=cut, end=end_date)

        for profile in run.payload.profiles:
            eligible = set(run.eligible_by_profile.get(profile.profile_id, []))
            eligible_returns = {cnpj: value for cnpj, value in realised.items() if cnpj in eligible}
            selected = [fund.cnpj_classe for fund in profile.top]
            outcomes.append(
                evaluate(
                    profile_id=profile.profile_id,
                    cut_date=cut,
                    selected=selected,
                    eligible_returns=eligible_returns,
                    benchmark_return=benchmark,
                    rules=rules,
                    stopped=[cnpj for cnpj in selected if cnpj in stopped],
                    fees=run.fees,
                    forward_returns_all=realised,
                )
            )
        del run

    shutil.rmtree(scratch, ignore_errors=True)
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
        "| Corte | Perfil | Top 5 rendeu | CDI | Mediana dos elegíveis | Vantagem "
        "| Contra o acaso | Contra os baratos | Bateram a mediana |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for outcome in sorted(outcomes, key=lambda item: (item.cut_date, item.profile_id)):
        mark = "✅" if outcome.random_percentile > result.threshold else "❌"
        lines.append(
            f"| {outcome.cut_date:%d/%m/%Y} | {outcome.profile_id} "
            f"| {outcome.selected_return:+.2%} | {outcome.benchmark_return:+.2%} "
            f"| {outcome.peer_median_return:+.2%} "
            f"| **{outcome.excess_over_median * 10_000:+.0f} pb** "
            f"| p{outcome.random_percentile:.0%} {mark} "
            f"| p{outcome.cheap_percentile:.0%} | {outcome.beat_median} de 5 |"
        )
    edges = [outcome.excess_over_median * 10_000 for outcome in outcomes]
    cheap = [outcome.cheap_percentile for outcome in outcomes]
    beat_median = sum(1 for outcome in outcomes if outcome.excess_over_median > 0)
    beat_benchmark = sum(1 for outcome in outcomes if outcome.excess_over_benchmark > 0)
    tested = len(outcomes)
    lines += [
        "",
        "**Contra o acaso** é a coluna que decide o veredito: em que percentil o Top 5 caiu "
        "numa distribuição de mil carteiras de cinco fundos sorteados do mesmo universo "
        "elegível naquela data. Bater a mediana dos pares é fácil; bater o sorteio não é.",
        "",
        "### O que os números dizem, sem arredondar para cima",
        "",
        f"A vantagem sobre a mediana dos elegíveis ficou entre **{min(edges):+.0f} e "
        f"{max(edges):+.0f} pontos-base**, e o Top 5 ficou acima dessa mediana em "
        f"**{beat_median} dos {tested} recortes**. "
        + (
            "Em mais da metade dos casos, portanto, escolher os cinco melhores pelo método "
            "rendeu **menos** que pegar o fundo do meio da lista."
            if beat_median * 2 < tested
            else "O saldo é positivo, mas por margens pequenas."
        ),
        "",
        f"Contra o CDI, o Top 5 ficou à frente em **{beat_benchmark} dos {tested} recortes**. "
        + (
            "Nenhum. Os fundos escolhidos renderam menos que o CDI em todos os cortes, o que "
            "não é surpresa num universo em que só 40% dos fundos bateram o CDI no ano — mas "
            "precisa estar escrito, porque é a comparação que o cliente faz de cabeça."
            if beat_benchmark == 0
            else "É a comparação que o cliente faz de cabeça, e por isso está na tabela."
        ),
        "",
        "Isso convive com percentis altos contra o sorteio sem contradição: fundos de renda "
        "fixa pós-fixados rendem todos perto do CDI, então a distribuição das carteiras "
        "aleatórias é muito estreita. Ficar num percentil alto de uma distribuição apertada "
        "significa ganhar de quase todo mundo **por muito pouco** — e ficar num percentil "
        "baixo significa perder de quase todo mundo, também por muito pouco. Nos dois casos, "
        "o que está em jogo são dezenas de pontos-base ao ano. Em renda fixa, onde a taxa "
        "mediana é 0,50% ao ano, é exatamente a ordem de grandeza do que há para ganhar — e "
        "é também pequeno o bastante para que três recortes não distingam método de sorte.",
        "",
        "### Contra os baratos: separando o que é seleção do que é aritmética",
        "",
        "A taxa de administração já sai da cota antes de qualquer medição. Como ela é o maior "
        "peso dos dois perfis, parte da vantagem sobre a mediana **não é escolha, é "
        "subtração**: fundo mais barato entrega mais do mesmo retorno bruto, e isso se sabia "
        "antes de rodar qualquer teste.",
        "",
        "A coluna **contra os baratos** repete o sorteio usando apenas o quartil mais barato "
        f"do mesmo universo. O Top 5 ficou entre **p{min(cheap):.0%} e p{max(cheap):.0%}** "
        "contra esse controle.",
        "",
        "**Leia essa coluna com cuidado, porque ela não é um experimento limpo.** Segurar o "
        "custo aproximadamente constante também muda a composição do grupo de comparação: o "
        "quartil mais barato é dominado por fundos de título público, que rendem bruto menos "
        "que os de crédito. Um percentil mais alto contra os baratos é, em parte, o Top 5 "
        "sendo comparado com fundos de risco menor. A coluna é um segundo ângulo sobre o "
        "mesmo resultado, não uma decomposição entre custo e habilidade.",
        "",
        "Ela é **reportada, não faz parte do critério**. O critério foi congelado antes de "
        "existir e continua sendo a comparação contra o universo inteiro.",
        "",
    ]
    carried = sorted({cnpj for outcome in outcomes for cnpj in outcome.carried})
    if carried:
        lines += (
            [
                "## Fundos escolhidos que saíram do universo elegível",
                "",
                "Mantidos na carteira pelo último valor conhecido, conforme a política "
                "congelada na configuração, e contados na média do Top 5. Tirá-los seria medir "
                "o método só pelos fundos que deram certo.",
                "",
            ]
            + [f"- `{cnpj}`" for cnpj in carried]
            + [""]
        )

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
