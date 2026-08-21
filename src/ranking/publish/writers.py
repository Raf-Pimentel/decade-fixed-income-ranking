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
from ranking.publish.format import money as _money
from ranking.publish.format import percent as _percent

SCHEMA_VERSION = "1.0.0"


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
    """The readable version.

    A plain list. The robustness simulation still decides the order — it runs
    on every fund and the five published are the ones that survived it — but
    "appeared in 42% of simulations" next to a fund name is noise for someone
    choosing where to put their emergency reserve. That number lives in
    `ranking.json` and in the technical section at the bottom, where the people
    who want to audit the method will look for it.
    """
    lines: list[str] = [
        "# Melhores fundos de renda fixa para o investidor de varejo",
        "",
        f"Data de referência: **{payload.reference_date:%d/%m/%Y}** · janela de "
        f"**{payload.lookback_months} meses** · referência de comparação: "
        f"**{payload.benchmark_label}**.",
        "",
        "Duas listas, porque a resposta depende de quando você precisa do dinheiro de volta.",
        "",
    ]

    for profile in payload.profiles:
        lines += [
            f"## {profile.label}",
            "",
            f"Escolhidos entre **{profile.eligible_universe_size} fundos** que um investidor de "
            "varejo consegue de fato comprar.",
            "",
            "| # | Fundo | Gestor | Taxa a.a. | Resgate | Rendeu em 12m | vs CDI |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
        for fund in profile.top:
            numbers = fund.metrics
            days = numbers.get("dias_resgate")
            prazo = f"D+{int(days)}" if isinstance(days, int | float) else "—"
            lines.append(
                f"| {fund.rank} | {fund.name[:46]} | {(fund.manager or '—')[:22]} "
                f"| {_percent(numbers.get('taxa_adm'), 3)} | {prazo} "
                f"| {_percent(numbers.get('retorno'))} | {_percent(numbers.get('excesso'))} |"
            )
        lines += ["", "### Por que cada um", ""]
        for fund in profile.top:
            lines += [f"**{fund.rank}. {fund.name}** — {fund.rationale}", ""]

    lines += [
        "---",
        "",
        "## O que você precisa saber antes de usar esta lista",
        "",
        "Duas limitações importam mais que todas as outras.",
        "",
        "**1. Este ranking não olha o que os fundos têm dentro.** Ele mede resultado, não "
        "conteúdo. Dois fundos com rentabilidade, oscilação e pior queda praticamente "
        "idênticos podem carregar riscos de crédito completamente diferentes — e crédito "
        "privado no Brasil paga um prêmio pequeno e constante por muitos meses e devolve tudo "
        "de uma vez quando o emissor quebra. Nada na série de cotas antecipa isso.",
        "",
        "**2. Doze meses de histórico não dizem o que acontece em 2026.** O método foi testado "
        "fora da amostra e funcionou em 2025 (ver `validacao.md`), mas 2025 teve um único "
        "regime de juros. É evidência, não garantia.",
        "",
        "### E três coisas que valem ser ditas",
        "",
        "**Os pesos são uma escolha, não uma dedução.** Custo pesa mais que rentabilidade "
        "passada porque a taxa é o único número que se sabe com certeza sobre o ano que vem — "
        "e porque apenas 40% dos fundos bateram o CDI em 2025. Mas não há demonstração de que "
        "esses pesos sejam ótimos. O que o projeto garante é que, informados outros pesos, o "
        "resultado sai coerente com eles: os pesos vivem em um arquivo de configuração.",
        "",
        "**A lista concentra em poucas gestoras.** É consequência coerente do critério: as "
        "gestoras dos grandes bancos praticam taxas muito baixas nos fundos de casa, e custo "
        "é o maior peso. Não é recomendação de concentrar — é o que o critério devolve.",
        "",
        "**A ordem entre os cinco não é forte.** Com doze meses de dados diários, a incerteza "
        "sobre o retorno ajustado ao risco é maior que a distância entre os primeiros "
        "colocados. A lista afirma que estes cinco se sustentam, não que o primeiro é melhor "
        "que o segundo.",
        "",
    ]

    if notes:
        lines += ["### Outras limitações", ""] + [f"- {note}" for note in notes] + [""]

    lines += [
        "---",
        "",
        "## Seção técnica",
        "",
        "O ranking foi reconstruído **1.000 vezes**, reamostrando as séries de retorno em "
        "blocos e sorteando os pesos dentro de faixas declaradas. Os cinco publicados são os "
        "que mais sobreviveram a esse teste, não os de maior nota pontual. A taxa de "
        "sobrevivência de cada um:",
        "",
        "| Fundo | Perfil | Nota | Apareceu no top 5 | Só pelo desempenho |",
        "|---|---|---:|---:|---:|",
    ]
    for profile in payload.profiles:
        for fund in profile.top:
            honest = (
                f"{fund.appearance_rate_variable_only:.0%}"
                if fund.appearance_rate_variable_only is not None
                else "—"
            )
            lines.append(
                f"| {fund.name[:40]} | {profile.profile_id} | {fund.score:.1f} "
                f"| {fund.appearance_rate:.0%} | {honest} |"
            )
    lines += [
        "",
        "**A última coluna responde outra pergunta:** este fundo continuaria no top 5 se "
        "fosse pontuado **só pelo desempenho** — retorno, ganho sobre o CDI, oscilação e "
        "pior queda — ignorando taxa e prazo de resgate?",
        "",
        "Para a maioria, a resposta é não. Isso não é defeito: é a consequência deliberada "
        "de dar à taxa o maior peso, porque ela é o único número que se sabe com certeza "
        "sobre o ano que vem, e porque apenas 40% dos fundos bateram o CDI em 2025. "
        "**Mas quem lê esta lista tem o direito de saber que ela é, em grande parte, um "
        "ranking de custo e liquidez** — e que os fundos escolhidos não seriam os mesmos "
        "se o critério fosse desempenho passado.",
        "",
        "Todos os números por fundo estão em `ranking.json`.",
        "",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(chr(10).join(lines), encoding="utf-8")
