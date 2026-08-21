"""The ranking as a page, regenerated on every run.

Built from the same payload as `ranking.json`, so the two cannot drift apart.
Entirely self-contained — no stylesheet, font or script from anywhere else —
because the moment someone needs it most is while presenting from a laptop
with no network.

The limitations sit on the page, next to the funds. A page that shows only the
winners would undo, in one screenshot, everything the rest of this project
says about being honest under uncertainty.
"""

from __future__ import annotations

import datetime as dt
from html import escape
from pathlib import Path

from ranking.contracts.schemas import RankedFund, RankingOutput
from ranking.publish.format import count as _count
from ranking.publish.format import money as _money
from ranking.publish.format import percent as _pct

_STYLE = """
:root {
  --bg: #fbfbfa; --card: #ffffff; --ink: #1a1a18; --soft: #6b6b66;
  --line: #e6e5e1; --accent: #1f6f5c; --warn: #8a5a1f; --shade: #f4f4f1;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16161a; --card: #1e1e23; --ink: #ececea; --soft: #9a9a95;
    --line: #2e2e35; --accent: #5fbfa3; --warn: #d9a25c; --shade: #24242a;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2.5rem 1.25rem 4rem; background: var(--bg); color: var(--ink);
  font: 16px/1.55 ui-sans-serif, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.wrap { max-width: 1080px; margin: 0 auto; }
header { border-bottom: 2px solid var(--ink); padding-bottom: 1.25rem; margin-bottom: 2rem; }
h1 { margin: 0 0 .4rem; font-size: 1.9rem; letter-spacing: -.02em; }
.sub { color: var(--soft); font-size: .95rem; }
.verdict {
  margin-top: 1rem; padding: .7rem .9rem; border-left: 3px solid var(--accent);
  background: var(--shade); font-size: .9rem; border-radius: 0 6px 6px 0;
}
section { margin-bottom: 2.5rem; }
h2 { font-size: 1.25rem; margin: 0 0 .25rem; }
.count { color: var(--soft); font-size: .9rem; margin: 0 0 1rem; }
.fund {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 1rem 1.1rem; margin-bottom: .7rem; display: grid;
  grid-template-columns: 2.2rem 1fr; gap: .9rem; align-items: start;
}
.pos { font-size: 1.5rem; font-weight: 700; color: var(--accent); line-height: 1.1; }
.name { font-weight: 650; margin-bottom: .15rem; }
.mgr { color: var(--soft); font-size: .82rem; margin-bottom: .7rem; }
.nums { display: flex; flex-wrap: wrap; gap: 1.4rem; margin-bottom: .6rem; }
.num { min-width: 5.5rem; }
.num .k { display: block; color: var(--soft); font-size: .7rem;
  text-transform: uppercase; letter-spacing: .05em; }
.num .v { font-variant-numeric: tabular-nums; font-weight: 600; font-size: 1.02rem; }
.why { font-size: .87rem; color: var(--soft); }
.caveats { background: var(--card); border: 1px solid var(--line);
  border-radius: 10px; padding: 1.2rem 1.3rem; }
.caveats h3 { margin: 0 0 .8rem; font-size: 1.05rem; }
.caveats p { margin: 0 0 .8rem; font-size: .89rem; }
.caveats p:last-child { margin-bottom: 0; }
.flag { color: var(--warn); font-weight: 650; }
footer { margin-top: 2.5rem; color: var(--soft); font-size: .78rem;
  border-top: 1px solid var(--line); padding-top: 1rem; }
@media (max-width: 620px) { .nums { gap: .9rem; } .num { min-width: 4.4rem; } }
"""


def _card(fund: RankedFund) -> str:
    numbers = fund.metrics
    days = numbers.get("dias_resgate")
    prazo = f"D+{int(days)}" if isinstance(days, int | float) else "—"
    holders = numbers.get("cotistas")
    cells = [
        ("rendeu 12m", _pct(numbers.get("retorno"))),
        ("sobre o CDI", _pct(numbers.get("excesso"))),
        ("taxa a.a.", _pct(numbers.get("taxa_adm"), 3)),
        ("resgate", prazo),
        ("pior queda", _pct(numbers.get("pior_queda"))),
        ("patrimônio", _money(numbers.get("patrimonio_medio"))),
        ("cotistas", _count(holders)),
    ]
    nums = "".join(
        f'<div class="num"><span class="k">{escape(key)}</span>'
        f'<span class="v">{escape(value)}</span></div>'
        for key, value in cells
    )
    return (
        f'<article class="fund"><div class="pos">{fund.rank}</div><div>'
        f'<div class="name">{escape(fund.name)}</div>'
        f'<div class="mgr">{escape(fund.manager or "gestor não informado")}'
        f" · {escape(fund.peer_group or 'sem grupo de pares')}</div>"
        f'<div class="nums">{nums}</div>'
        f'<div class="why">{escape(fund.rationale)}</div>'
        f"</div></article>"
    )


def write_html(payload: RankingOutput, path: Path, validation: str | None = None) -> None:
    """Render the ranking to a single self-contained file."""
    sections: list[str] = []
    for profile in payload.profiles:
        cards = "".join(_card(fund) for fund in profile.top)
        sections.append(
            f"<section><h2>{escape(profile.label)}</h2>"
            f'<p class="count">Escolhidos entre {profile.eligible_universe_size} fundos que um '
            f"investidor de varejo consegue de fato comprar.</p>{cards}</section>"
        )

    verdict = (
        f'<div class="verdict"><strong>Testado fora da amostra.</strong> {escape(validation)}</div>'
        if validation
        else ""
    )

    body = f"""<div class="wrap">
<header>
  <h1>Melhores fundos de renda fixa</h1>
  <div class="sub">Data de referência <strong>{payload.reference_date:%d/%m/%Y}</strong>
    · janela de {payload.lookback_months} meses
    · comparados ao {escape(payload.benchmark_label)}
    · gerado em {dt.datetime.now():%d/%m/%Y %H:%M}</div>
  {verdict}
</header>
{"".join(sections)}
<section class="caveats">
  <h3>O que esta lista não sabe</h3>
  <p><span class="flag">Não olha a carteira dos fundos.</span> Mede resultado, não
     conteúdo. Dois fundos com números praticamente idênticos podem carregar riscos de
     crédito completamente diferentes — e crédito privado paga um prêmio pequeno e constante
     por muitos meses e devolve tudo de uma vez quando o emissor quebra.</p>
  <p><span class="flag">Doze meses não dizem o que acontece em 2026.</span> O método foi
     testado fora da amostra e funcionou em 2025, mas 2025 teve um único regime de juros.
     É evidência, não garantia.</p>
  <p><strong>Os pesos são uma escolha, não uma dedução.</strong> Custo pesa mais que
     rentabilidade passada porque a taxa é o único número que se sabe com certeza sobre o ano
     que vem, e porque apenas 40% dos fundos bateram o CDI em 2025. Não há demonstração de
     que sejam ótimos — eles vivem em um arquivo de configuração, e o resultado acompanha
     quem os mudar.</p>
  <p><strong>A ordem entre os cinco não é forte.</strong> A incerteza sobre o retorno
     ajustado ao risco é maior que a distância entre os primeiros colocados. A lista afirma
     que estes cinco se sustentam, não que o primeiro é melhor que o segundo.</p>
</section>
<footer>Gerado pelo pipeline a cada execução, a partir dos mesmos dados de
  <code>ranking.json</code>. Fontes públicas da CVM e do Banco Central.
  Estudo de caso — não é recomendação de investimento.</footer>
</div>"""

    page = (
        "<!doctype html>\n"
        '<html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>Ranking de fundos de renda fixa — {payload.reference_date:%d/%m/%Y}</title>"
        f"<style>{_STYLE}</style></head><body>{body}</body></html>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
