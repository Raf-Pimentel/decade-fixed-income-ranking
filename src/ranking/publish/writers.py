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
        # Reported plainly, not ranked: the fee no longer scores a fund (D-051),
        # it only gates the finalists, so there is no cost percentile to place it
        # against.
        parts.append(f"taxa de {_percent(fee, 3)} ao ano")
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
                "universo de onde ela saiu. Ela está refletindo o mercado que o investidor "
                "de varejo tem.",
                "",
            ]
        explained.add("concentracao")

    if profile.displaced:
        lines += [
            "**Fundos deixados de fora por repetirem outro da lista.** Mesma gestora, e "
            "séries de cota que diferem por menos de 0,10% ao ano de oscilação. É uma "
            "carteira só, vendida com dois nomes. O cliente que comprasse os dois teria uma "
            "exposição, e não duas.",
            "",
        ]
        for item in profile.displaced:
            lines += [
                f"- *{item.name}* (nota {item.score:.1f}) repete **{item.duplicate_of}**. "
                f"As duas séries diferem em {item.tracking_difference:.4%} ao ano.",
            ]
        lines += [""]

    if profile.cost_excluded:
        lines += [
            "**Fundos que a nota alcançou e o porteiro de custo barrou.** A taxa não pontua o "
            "fundo (ela é medida com incerteza), mas um custo alto demais tira o fundo da "
            "lista. O custo usado é o número confiável de cada caso: a taxa declarada, ou a "
            "medida quando a declarada é a baixa demais para ser verdade.",
            "",
        ]
        for gated in profile.cost_excluded:
            lines += [
                f"- *{gated.name}* barrado por custo de {gated.custo_porteiro:.3%} ao ano "
                "(acima do teto).",
            ]
        lines += [""]

    if profile.performance_excluded:
        lines += [
            "**Fundos que a nota alcançou e o piso de performance barrou.** Um fundo batido pela "
            "maioria dos próprios pares no ganho sobre o CDI sai da lista, por mais barato, "
            "antigo ou estável que seja. É a bandeira vermelha que nenhuma outra virtude cobre.",
            "",
        ]
        for flagged in profile.performance_excluded:
            lines += [
                f"- *{flagged.name}* barrado por ficar no percentil "
                f"{flagged.excess_percentile:.0%} de ganho sobre o CDI dentro do próprio grupo.",
            ]
        lines += [""]

    if profile.inert_metrics:
        named = ", ".join(f"`{name}`" for name in profile.inert_metrics)
        lines += [
            f"**Peso redistribuído.** {named} não separa nada dentro deste universo. A "
            "elegibilidade já filtrou por esse critério, e quase todos os fundos que "
            "sobraram empatam nele. O peso foi para os critérios que ainda distinguem, e os "
            f"pesos de fato aplicados são {_weights(profile.effective_weights)}.",
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

    A plain list. The robustness simulation still decides the order, since it
    runs on every fund and the five published are the ones that survived it.
    But "appeared in 42% of simulations" next to a fund name is noise for
    someone choosing where to put their emergency reserve. That number lives in
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
            lines += [f"**{fund.rank}. {fund.name}.** {fund.rationale}", ""]
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
        "idênticas podem carregar riscos de crédito bem diferentes. Crédito privado no Brasil "
        "paga um prêmio pequeno e constante por muitos meses, e devolve tudo de uma vez "
        "quando o emissor quebra. Nada na série de cotas antecipa isso.",
        "",
        f"**2. {payload.lookback_months} meses de histórico não dizem o que acontece em 2026.** "
        "O método foi testado fora da amostra e funcionou em 2025 (ver `validacao.md`), mas "
        "2025 teve um único regime de juros. É evidência, não garantia.",
        "",
        "### E três coisas que valem ser ditas",
        "",
        "**Os pesos são uma escolha, não uma dedução.** O risco lidera os dois perfis: a taxa "
        "saiu do score e virou porteiro, porque ela é medida com incerteza e um peso fino "
        "sobre ela ranqueava fundos no ruído (ver D-051). Ainda assim, não há demonstração de "
        "que esses pesos sejam os melhores possíveis. O que o projeto garante é que, "
        "informados outros pesos, o resultado sai coerente com eles. Os pesos ficam em um "
        "arquivo de configuração.",
        "",
        "**A lista pode concentrar em poucas gestoras.** É consequência do universo, não uma "
        "recomendação de concentrar: quando uma casa responde por boa parte dos fundos "
        "elegíveis, uma lista tirada dele a repete. A concentração de cada perfil está dita "
        "ao lado da própria lista.",
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
        "| Só desempenho e risco |",
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
        "perfil**. Quando as duas se afastam, o fundo é o melhor de um grupo que não é bom, "
        "e quem lê tem o direito de saber disso antes de comprar.",
    ]
    lines += [
        "",
        "**A última coluna responde outra pergunta:** este fundo continuaria no top 5 se "
        "fosse pontuado **só por desempenho e risco** — retorno, ganho sobre o CDI, oscilação "
        "e pior queda — ignorando o tamanho e o prazo de resgate?",
        "",
        "A taxa já não está no score: ela saiu de vez e virou porteiro (ver D-051), então a "
        "lista não é mais, como era antes, em grande parte um ranking de custo. Esta coluna "
        "mostra o que sobra quando também se ignora o tamanho do fundo. Onde ela acompanha a "
        "coluna anterior, a posição vem do desempenho e do risco, e não de o fundo ser grande.",
        "",
        "Todos os números por fundo estão em `ranking.json`.",
        "",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(chr(10).join(lines), encoding="utf-8")


def write_comparison(
    payload: RankingOutput,
    profiles: list[tuple[str, list[RankedFund]]],
    path: Path,
) -> None:
    """A longer list, for holding this ranking against the ones the market publishes.

    Ten names rather than five, drawn from the same walk down the same ranked
    order, so the first five are the five that were delivered. This is not a
    second answer and it is not a recommendation: five is what the method says
    it can defend, and the sixth to tenth are here so that a reader comparing
    against a published ranking has more than five names to match on.

    The delivery is `ranking.md`. Nothing in this file feeds back into it.
    """
    delivered = payload.profiles[0].top_n if payload.profiles else 5
    lines: list[str] = [
        f"# Os {max((len(f) for _, f in profiles), default=0)} primeiros, para comparação",
        "",
        f"Data de referência: **{payload.reference_date:%d/%m/%Y}**. Os **{delivered} primeiros "
        f"de cada lista são o que foi entregue** em `ranking.md`, na mesma ordem. Os seguintes "
        "existem para comparar este ranking com os que o mercado publica, e não são "
        "recomendação: cinco é o tamanho que o método afirma sustentar.",
        "",
    ]
    for label, funds in profiles:
        lines += [
            f"## {label}",
            "",
            "| # | Fundo | Gestor | Taxa a.a. | Resgate | Rendeu | vs CDI | Nota grupo | "
            "Nota universo | Apareceu |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for position, fund in enumerate(funds, start=1):
            numbers = fund.metrics
            days = numbers.get("dias_resgate")
            prazo = f"D+{int(days)}" if isinstance(days, int | float) else "—"
            mark = "" if position <= delivered else " *"
            lines.append(
                f"| {position}{mark} | {fund.name[:44]} | {(fund.manager or '—')[:20]} "
                f"| {_percent(numbers.get('taxa_adm'), 3)} | {prazo} "
                f"| {_percent(numbers.get('retorno'))} | {_percent(numbers.get('excesso'))} "
                f"| {fund.score:.1f} | {fund.score_pool:.1f} "
                f"| {fund.appearance_rate:.0%} |"
            )
        lines += ["", f"\* fora do Top {delivered} entregue.", ""]

    lines += [
        "---",
        "",
        "As mesmas ressalvas de `ranking.md` valem aqui, e uma a mais: a taxa de aparição na "
        f"última coluna mede quantas vezes o fundo terminou entre os **{delivered} primeiros** "
        "das mil simulações, não entre os dez. Um fundo em oitavo com aparição baixa não é um "
        "oitavo estável, é um fundo que raramente chegou ao topo.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
