# Brazilian Fixed-Income Fund Ranking

[![CI](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/ci.yml/badge.svg)](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/ci.yml)
[![Weekly ranking](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/weekly-ranking.yml/badge.svg)](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/weekly-ranking.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

Ranks Brazilian fixed-income funds and returns the top five for each retail client
profile, from public CVM and Central Bank data, for any reference date.

Built for a case study with a reference period of **31 December 2025**.

## Quick start

Needs [uv](https://github.com/astral-sh/uv) installed. Nothing else.

```bash
uv sync
uv run ranking --reference-date 2025-12-31
```

One command, about 40 seconds from a cold cache. It downloads roughly 280 MB, validates
6.3 million rows, and writes to [`saida/`](saida):

| File                                                      | Contains                                                                            |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [`ranking.md`](saida/ranking.md)                         | the two top-five lists and why each fund is there                                   |
| [`ranking.json`](saida/ranking.json)                     | the same, plus every metric, percentile and source hash, for another system to read |
| [`ranking.html`](saida/ranking.html)                     | the same lists as a self-contained page                                             |
| [`relatorio_qualidade.md`](saida/relatorio_qualidade.md) | the eligibility funnel against its expected baseline                                |
| [`validacao.md`](saida/validacao.md)                     | the out-of-sample test                                                              |

Those files are committed: a deliverable that only exists after someone runs the
pipeline is not delivered.

Add `--validate` to also rebuild the ranking as of each frozen cut date and measure what
followed. Minutes rather than seconds, because it runs the whole pipeline four times.

```bash
uv run ranking --reference-date 2025-12-31 --validate
```

Or with nothing installed but Docker:

```bash
docker build -t fixed-income-ranking .
docker run --rm -v "$PWD/saida:/app/saida" fixed-income-ranking --reference-date 2025-12-31
```

## What it does

Given a reference date, the pipeline:

1. **downloads** the CVM daily reports, registry, statements and factsheets, plus the
   Central Bank's CDI series;
2. **validates** every row against a declared schema, sending failures to quarantine *with a
   written reason* and stopping the run outright if more than 5% is unusable;
3. **selects** the funds a retail investor can actually buy (36,594 registered classes
   become 580), checking the count at each step against a baseline measured in advance;
4. **measures** return, risk, cost and liquidity figures per fund over a window exactly
   as long as its label says, from the daily quota, which already comes net of fees;
5. **ranks** each fund against funds *like it*, weighted per profile, moving any weight
   whose criterion the eligible pool ties on to the criteria that still discriminate;
6. **picks five funds rather than five scores**, passing over any fund that repeats a
   portfolio already on the list;
7. **tests whether the answer holds** by rebuilding the ranking a thousand times.

Every number that decides anything lives in [`configs/`](configs), not in code.
The design is written up in [`docs/01-solution-design.md`](docs/01-solution-design.md).

## The two profiles

The split is by **when the client needs the money back**, because 58% of the retail universe
redeems same-day and a single list would hand the same five funds to someone saving for a
holiday and someone saving for three years.

|                    | Emergency reserve            | Two years or more                        |
| ------------------ | ---------------------------- | ---------------------------------------- |
| Redemption         | up to D+1                    | up to D+30                               |
| Minimum investment | ≤ R$ 5,000                   | ≤ R$ 50,000                              |
| Eligible funds     | 218                          | 390                                      |
| Heaviest weight    | admin fee                    | admin fee                                |
| Then               | volatility, worst fall       | excess over CDI, return per unit of risk |

Cost outweighs past return in both. The fee is the only number known with certainty about
next year, and only 40% of funds beat the CDI in 2025. The weights are a declared choice
rather than a derivation, and the ones actually applied are published beside the ones
declared: a criterion the eligible pool ties on cannot separate anything, so its weight moves
to the criteria that still can, and `ranking.json` names it.

## One portfolio, one slot

A manager routinely runs a single portfolio and sells it through a row of distribution
wrappers — Caixa offers a dozen over one fixed-income portfolio. Each is a separate class,
each is eligible, and each earns nearly the same score, so a top five holding two of them
offers four exposures and does not say so.

Two funds count as one when the same manager runs both **and** the annualised volatility of
the difference between their daily returns is near zero — two wrappers of one portfolio
differ only by their fee, a constant drag that contributes no variance. Correlation cannot do
this job here and is deliberately not used: every post-fixed fund follows the same overnight
curve and correlates above 0.99 with every other, so a threshold high enough to catch a twin
marks half this universe as duplicated.

A fund passed over is published beside the list, named, with the fund it repeats and the
distance between them.

## Does it work?

Full test in [`saida/validacao.md`](saida/validacao.md).

The ranking was rebuilt as of 31 March, 30 June and 30 September 2025, using nothing
published after each date, and the chosen funds were measured to the end of the year against
the median of the eligible universe, against the CDI, and against 1,000 random five-fund
portfolios drawn from that same universe.

| Profile           | Beat 1,000 random five-fund portfolios on | Edge over the median |
| ----------------- | ----------------------------------------- | -------------------- |
| Emergency reserve | 2 of 3 dates (p68, p99, p22) | −15 to +21 bp       |
| Two years or more | 3 of 3 dates (p71, p94, p72) | −4 to +21 bp        |

## Development

```bash
uv run pytest                     # 288 tests
uv run pytest -m trap             # the CVM data-trap regressions
uv run pytest -m invariant        # the financial invariants
uv run ruff check . && uv run mypy src
```

Most tests check a component against a fixture, which catches a wrong formula.
`tests/integration/test_published_output.py` opens the delivered `ranking.json` and asserts
against the product instead — that the window is as long as its label claims, that no list
holds one portfolio twice, that every weight does something, that no published field is a
placeholder. Those failures never break a function, so a suite that only looks inward stays
green through all of them.

Every push runs lint, types, the suite and a Docker build on a blank runner.
[`weekly-ranking.yml`](.github/workflows/weekly-ranking.yml) runs the whole pipeline against
live data every Monday and commits a fresh ranking into `saida/`, unattended.

## Scaling to a daily cadence

A single node running Polars, with no orchestrator, because the volume does not require one.
What makes that viable:

- **Parsing happens once.** Each file is cached as Parquet under a name carrying the source
  file's SHA-256, so a restated archive misses the cache and is parsed again, where a
  name-keyed cache would serve stale numbers forever.
- **The panel is assembled by scanning columnar files**, rather than holding a dozen decoded
  frames open at once.
- **Point-in-time is enforced in three places**, which is what makes a run for any past date
  a single command.

## Data sources

All public, no credentials. What was deliberately not used, and why, is in
[`configs/sources.yaml`](configs/sources.yaml).

| Source                      | Provides                                                                                |
| --------------------------- | --------------------------------------------------------------------------------------- |
| CVM daily report            | quota, net assets, shareholders, subscriptions, redemptions                             |
| CVM registry (RCVM 175)     | classification, target investor, open/closed, exclusive                                 |
| CVM statement and factsheet | admin fee, redemption terms, minimum investment                                         |
| Central Bank series 12      | daily CDI                                                                               |
| ANBIMA                      | the fund classification that defines peer groups, which arrives inside the CVM registry |

## Reading the project

| Document | Contains |
| --- | --- |
| [`docs/03-guia-de-defesa.md`](docs/03-guia-de-defesa.md) | short version: the numbers, ten questions and their answers         |
| [`docs/01-solution-design.md`](docs/01-solution-design.md) | the design, in Portuguese                                             |
| [`docs/decisoes.md`](docs/decisoes.md)                     | every decision taken, including the ones later reversed                     |
| [`docs/02-checklist.md`](docs/02-checklist.md)             | what was done, and what was not                                |
| `CLAUDE.md`                                                | the working agreement: rules, the thirteen data traps, the quality baseline  |

The decision log records what was measured before each choice,
and what was got wrong, including guardrails that failed, and a first bad ranking.

## What this does not do

- **It does not look inside the portfolios.** It measures only outcomes, so two
  funds with the same return and risk are indistinguishable to it even if one holds Treasury
  paper and the other private credit. The CVM publishes this (CDA); it is the first item of
  future work.
- **It cannot see funds that closed.** It measures the past, in one interest-rate regime,
  and the universe is optimistic by construction.
- **It compares inflation-linked funds against CDI**, because ANBIMA publishes the IMA as a
  snapshot of the current day rather than as history. Affects 8% of the universe.
- **It counts the fee twice on purpose** — once inside the net quota, once as the heaviest
  weight — because the second counting is the one that speaks about next year.
- **It reports before income tax.** Most funds follow the same regressive table and their
  relative order holds; funds built on incentivised infrastructure debt are exempt for
  individuals, so every fund publishes its regime.
- **It evaluates each fund on its own**, not as a portfolio, beyond refusing to hold the
  same portfolio twice.