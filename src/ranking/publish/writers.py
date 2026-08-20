"""Writing the two things anyone actually reads.

`ranking.json` is for another system and is validated against a versioned
contract before it is written. `ranking.md` is for a person, and its job is to
make the reasoning arguable: every fund carries the numbers that put it there,
and the caveats sit next to the list rather than in a footnote nobody reaches.
"""

from __future__ import annotations

import json
from pathlib import Path

from ranking.contracts.schemas import RankedFund, RankingOutput

SCHEMA_VERSION = "1.0.0"


def _percent(value: object, places: int = 2) -> str:
    """Anything that is not a number prints as a dash rather than crashing the
    report — a missing figure is information, not a failure."""
    if not isinstance(value, int | float) or isinstance(value, bool):
        return "—"
    return f"{value * 100:.{places}f}%"


def _money(value: object) -> str:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return "—"
    if value >= 1e9:
        return f"R$ {value / 1e9:.1f} bi"
    if value >= 1e6:
        return f"R$ {value / 1e6:.0f} mi"
    return f"R$ {value:,.0f}"


def describe(fund: RankedFund) -> str:
    """A sentence that says why this fund is here, built from its own numbers.

    Written from the figures rather than from adjectives, so that it cannot
    drift away from what the data says. If a fund is expensive and still
    ranked, the sentence says it is expensive.
    """
    numbers = fund.metrics
    parts: list[str] = []

    fee = numbers.get("taxa_adm")
    if isinstance(fee, float):
        cheap = fund.percentiles.get("admin_fee", 0.5)
        how = "entre as mais baratas" if cheap >= 0.75 else "cara" if cheap <= 0.25 else "mediana"
        parts.append(f"taxa de {_percent(fee, 3)} ao ano, {how} do grupo")
    elif numbers.get("taxa_zero_declarada"):
        # Reported, not scored: the fee is charged somewhere we cannot see.
        parts.append("taxa declarada de zero, provavelmente cobrada no fundo investidor")

    days = numbers.get("dias_resgate")
    if isinstance(days, int | float):
        parts.append("resgate no mesmo dia" if days == 0 else f"resgate em D+{int(days)}")

    excess = numbers.get("excesso")
    if isinstance(excess, float):
        verb = "acima" if excess >= 0 else "abaixo"
        parts.append(f"{_percent(abs(excess))} {verb} do CDI em 12 meses")

    fall = numbers.get("pior_queda")
    if isinstance(fall, float):
        parts.append(
            "nunca caiu no período" if fall >= -1e-6 else f"pior queda de {_percent(abs(fall))}"
        )

    assets = numbers.get("patrimonio_medio")
    if isinstance(assets, float):
        parts.append(f"patrimônio de {_money(assets)}")

    joined = "; ".join(parts)
    # Only the first letter: `.capitalize()` would lower-case the rest and
    # turn "CDI" into "cdi" and "R$" into "r$".
    sentence = joined[:1].upper() + joined[1:] + "."
    return f"{sentence} Apareceu no top 5 em {fund.appearance_rate:.0%} das simulações."


def write_json(payload: RankingOutput, path: Path) -> None:
    """Validated on the way out, so a malformed file is never published."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = payload.model_dump(mode="json")
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False, sort_keys=True) + "\n", "utf-8")


def write_markdown(payload: RankingOutput, path: Path, notes: list[str] | None = None) -> None:
    """The readable version, with the caveats beside the list and not below it."""
    lines: list[str] = [
        "# Melhores fundos de renda fixa — 31/12/2025",
        "",
        f"Data de referência: **{payload.reference_date:%d/%m/%Y}** · "
        f"janela de **{payload.lookback_months} meses** · "
        f"benchmark: **{payload.benchmark_label}**.",
        "",
        "> **A ordem entre os cinco não é significativa.** Com doze meses de dados diários, a "
        "incerteza sobre o retorno ajustado ao risco é maior que as diferenças entre eles. "
        "O que a lista afirma é que estes cinco se sustentam, não que o primeiro é melhor que "
        "o segundo. A taxa de aparição ao lado de cada fundo é a medida disso.",
        "",
    ]

    for profile in payload.profiles:
        pesos = " · ".join(
            f"{name} {weight}"
            for name, weight in sorted(profile.weights.items(), key=lambda kv: -kv[1])
        )
        lines += [
            f"## {profile.label}",
            "",
            f"{profile.eligible_universe_size} fundos elegíveis. Pesos: {pesos}.",
            "",
            "| # | Fundo | Gestor | Grupo | Taxa | Resgate | Sobre o CDI | Nota | Aparição |",
            "|---:|---|---|---|---:|---:|---:|---:|---:|",
        ]
        for fund in profile.top:
            numbers = fund.metrics
            days = numbers.get("dias_resgate")
            lines.append(
                f"| {fund.rank} | {fund.name[:44]} | {(fund.manager or '—')[:24]} "
                f"| {(fund.peer_group or '—')[:34]} "
                f"| {_percent(numbers.get('taxa_adm'))} "
                f"| D+{int(days) if isinstance(days, int | float) else '—'} "
                f"| {_percent(numbers.get('excesso'))} "
                f"| {fund.score:.1f} | {fund.appearance_rate:.0%} |"
            )
        lines += ["", "### Por que cada um", ""]
        for fund in profile.top:
            lines += [f"**{fund.rank}. {fund.name}** — {fund.rationale}", ""]

    if notes:
        lines += ["---", "", "## O que esta lista não sabe", ""]
        lines += [f"- {note}" for note in notes]
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
