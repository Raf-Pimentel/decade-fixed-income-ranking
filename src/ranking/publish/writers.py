"""Writing the two things anyone actually reads.

`ranking.json` is for another system and is validated against a versioned
contract before it is written. `ranking.md` is for a person, and its job is to
make the reasoning arguable: every fund carries the numbers that put it there,
and the caveats sit next to the list rather than in a footnote nobody reaches.
"""

from __future__ import annotations

import json
from pathlib import Path

from ranking.contracts.schemas import ProfileRanking, RankedFund, RankingOutput
from ranking.publish.format import money as _money
from ranking.publish.format import percent as _percent

SCHEMA_VERSION = "1.1.0"


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
        parts.append(f"{_percent(abs(excess))} {verb} do CDI na janela")

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


def _weights(weights: dict[str, int]) -> str:
    """Weights as a line a person can read, heaviest first."""
    ordered = sorted(weights.items(), key=lambda item: -item[1])
    return " · ".join(f"`{name}` {weight}" for name, weight in ordered)


def _profile_footnotes(profile: ProfileRanking, explained: set[str]) -> list[str]:
    """What shaped this particular list, said next to the list itself.

    Three things a reader cannot infer from five names and their numbers: how
    concentrated the universe they were drawn from already was, which funds
    were passed over for duplicating one already on the list, and which
    weighted criterion turned out to have nothing to say once eligibility had
    done its work.

    The document is read top to bottom, and the concentration behind both
    profiles has the same cause, so the argument is made once and afterwards
    only pointed at. `explained` carries what earlier lists already said. A
    caveat repeated word for word reads as a generator with nothing to say,
    and teaches the reader to skim the ones that appear only once.
    """
    lines: list[str] = []

    if profile.manager_share:
        biggest, share = max(profile.manager_share.items(), key=lambda item: item[1])
        if "concentracao" in explained:
            lines += [
                f"> **Concentração, de novo.** Como no perfil anterior, {biggest.title()} é a "
                f"maior gestora deste universo, com **{share:.1%}** dos "
                f"{profile.eligible_universe_size} fundos elegíveis.",
                "",
            ]
        else:
            lines += [
                f"> **De onde vem a concentração.** A maior gestora deste universo é "
                f"{biggest.title()}, com **{share:.1%}** dos {profile.eligible_universe_size} "
                "fundos elegíveis. Uma lista que a repete não está concentrando mais do que o "
                "universo de onde ela saiu — está refletindo o mercado que o investidor de "
                "varejo tem.",
                "",
            ]
        explained.add("concentracao")

    if profile.displaced:
        lines += [
            "**Fundos deixados de fora por repetirem outro da lista.** Mesma gestora e séries "
            "de cota que diferem por menos de 0,10% ao ano de oscilação: é uma carteira só, "
            "vendida com dois nomes. O cliente que comprasse os dois teria uma exposição, não "
            "duas.",
            "",
        ]
        for item in profile.displaced:
            lines += [
                f"- *{item.name}* (nota {item.score:.1f}) — repete **{item.duplicate_of}**; "
                f"as duas séries diferem em {item.tracking_difference:.4%} ao ano.",
            ]
        lines += [""]

    if profile.inert_metrics:
        named = ", ".join(f"`{name}`" for name in profile.inert_metrics)
        lines += [
            f"**Peso redistribuído.** {named} não separa nada dentro deste universo — a "
            "elegibilidade já filtrou por esse critério, e quase todos os fundos que sobraram "
            "empatam nele. O peso foi para os critérios que ainda distinguem, e os pesos de "
            f"fato aplicados são {_weights(profile.effective_weights)}.",
            "",
        ]
    return lines


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
        f"**{payload.lookback_months} meses**"
        + (
            f" ({payload.window_start:%d/%m/%Y} a {payload.reference_date:%d/%m/%Y})"
            if payload.window_start
            else ""
        )
        + f" · referência de comparação: **{payload.benchmark_label}**.",
        "",
        "Duas listas, porque a resposta depende de quando você precisa do dinheiro de volta.",
        "",
    ]

    months = payload.lookback_months
    explained: set[str] = set()
    for profile in payload.profiles:
        lines += [
            f"## {profile.label}",
            "",
            f"Escolhidos entre **{profile.eligible_universe_size} fundos** que um investidor de "
            "varejo consegue de fato comprar.",
            "",
            f"| # | Fundo | Gestor | Taxa a.a. | Resgate | Rendeu em {months}m | vs CDI |",
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
        lines += _profile_footnotes(profile, explained)

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
        f"**2. {payload.lookback_months} meses de histórico não dizem o que acontece em 2026.** "
        "O método foi testado fora da amostra e funcionou em 2025 (ver `validacao.md`), mas "
        "2025 teve um único regime de juros. É evidência, não garantia.",
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
        f"**A ordem entre os cinco não é forte.** Com {payload.lookback_months} meses de dados "
        "diários, a incerteza sobre o retorno ajustado ao risco é maior que a distância entre "
        "os primeiros colocados. A lista afirma que estes cinco se sustentam, não que o "
        "primeiro é melhor que o segundo.",
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
        "| Fundo | Perfil | Nota no grupo | Nota no universo | Apareceu no top 5 "
        "| Só pelo desempenho |",
        "|---|---|---:|---:|---:|---:|",
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
                f"| {fund.score_pool:.1f} | {fund.appearance_rate:.0%} | {honest} |"
            )
    lines += [
        "",
        "**Duas notas, porque o percentil é sempre relativo a alguma coisa.** A primeira "
        "compara o fundo com os pares da mesma categoria ANBIMA, que é a pergunta certa para "
        "não premiar quem simplesmente tomou mais risco de crédito. Ela é também silenciosa "
        "sobre a qualidade da categoria: ser o primeiro de dezoito vale 1 num grupo forte e "
        "num grupo fraco. A segunda nota refaz a conta contra **todo o universo elegível do "
        "perfil**. Quando as duas se afastam, o fundo é o melhor de um grupo que não é bom — "
        "e quem lê tem o direito de saber disso antes de comprar.",
    ]
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
