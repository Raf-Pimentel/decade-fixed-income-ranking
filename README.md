# Brazilian Fixed-Income Fund Ranking

[![CI](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/ci.yml/badge.svg)](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/ci.yml)
[![Weekly ranking](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/weekly-ranking.yml/badge.svg)](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/weekly-ranking.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

This project ranks Brazilian fixed-income funds and returns the top five for each retail
client profile, using public data from the CVM and the Central Bank. It works for any
reference date.

It was built for a case study with a reference period of **31 December 2025**.

## Video walkthrough

[**Watch the 5-minute walkthrough**](https://www.youtube.com/watch?v=c7FcTKU88tU) — the design,
the decision I am least sure about, and the path to production.

## Quick start

You need [uv](https://github.com/astral-sh/uv) installed. Nothing else.

```bash
uv sync
uv run ranking --reference-date 2025-12-31
```

That is one command and it takes about 40 seconds from a cold cache. It downloads roughly
280 MB, validates 6.3 million rows, and writes five files into [`saida/`](saida):

| File | Contains |
| --- | --- |
| [`ranking.md`](saida/ranking.md) | the two top-five lists and why each fund is on them |
| [`ranking.json`](saida/ranking.json) | the same lists plus every metric, percentile and source hash, for another system to read |
| [`ranking.html`](saida/ranking.html) | the same lists as a self-contained page |
| [`relatorio_qualidade.md`](saida/relatorio_qualidade.md) | the eligibility funnel compared against its expected baseline |
| [`validacao.md`](saida/validacao.md) | the out-of-sample test |
| [`top10.md`](saida/top10.md) | ten funds per profile instead of five, for holding this ranking against the ones the market publishes |

Those files are committed to the repository.

The answer is the top five. `top10.md` exists because comparing a list of five against a
published ranking of twenty-five is awkward, and it is built from the same walk down the same
ranked order, so it opens with exactly the five that were delivered. Anything past the fifth
row is marked, and a test fails if the two lists ever disagree.

If you add `--validate`, the pipeline also rebuilds the ranking as of each frozen cut date
and measures what happened afterwards. This takes minutes instead of seconds, because it runs
everything four times.

```bash
uv run ranking --reference-date 2025-12-31 --validate
```

You can also run it with nothing installed except Docker:

```bash
docker build -t fixed-income-ranking .
docker run --rm -v "$PWD/saida:/app/saida" fixed-income-ranking --reference-date 2025-12-31
```

## What it does

Given a reference date, the pipeline:

1. **downloads** the CVM daily reports, registry, statements and factsheets, along with the
   Central Bank's CDI series;
2. **validates** every row against a declared schema. Rows that fail go to quarantine with a
   written reason, and the run stops altogether if more than 5% of a file is unusable;
3. **selects** the funds a retail investor can actually buy, which takes 36,594 registered
   classes down to 472, and checks the count at each step against a baseline measured in
   advance. The last step asks who is inside a fund rather than what the fund is: a class with
   no individual and no distributor among its shareholders is not a product a person buys,
   whatever its regulation permits;
4. **measures** return, risk, cost and liquidity for each fund over a window that is exactly
   as long as its label says, using the daily quota, which already comes net of fees. The
   fee itself is measured too, against the fund each class holds, rather than read off the
   form the class filed;
5. **ranks** each fund against funds like it, weighted by profile. If a criterion turns out
   to be a tie across the whole eligible pool, its weight moves to the criteria that can
   still tell funds apart;
6. **picks five funds rather than five scores**, skipping any fund that repeats a portfolio
   already on the list;
7. **checks whether the answer holds** by rebuilding the ranking a thousand times.

Every number that decides anything lives in [`configs/`](configs) rather than in the code.
The design is written up in [`docs/01-solution-design.md`](docs/01-solution-design.md).

## The two profiles

The split is by when the client needs the money back. 58% of the retail universe pays out
within a day (D+0 or D+1), and a single list would hand the same five funds to someone saving
for a holiday and someone saving for three years.

| | Emergency reserve | Two years or more |
| --- | --- | --- |
| Redemption | up to D+1 | up to D+30 |
| Minimum investment | ≤ R$ 5,000 | ≤ R$ 50,000 |
| Eligible funds | 165 | 313 |
| Heaviest weight | volatility | return per unit of risk |
| Then | worst fall, size | worst fall, excess over CDI |
| Cost | a gate above 1%/yr, not a weight | a gate above 1%/yr, not a weight |

Risk leads both profiles. The fee no longer scores a fund: it is measured with uncertainty, so
it became a gate that strikes any finalist above 1% a year rather than a fine weight (D-051).
The concern about cost is still real — only 40% of funds beat the CDI in 2025 — which is why the
gate keeps the egregiously expensive out.

The weights are a declared choice rather than something derived, and the ones actually
applied are published next to the ones declared. A criterion that every eligible fund ties on
cannot separate anything, so its weight moves to the criteria that still can, and
`ranking.json` says which criterion this happened to.

## The fee is measured, not read

Cost still matters to a retail client, but it is measured with uncertainty, so it gates the
finalists rather than scoring them (see the note above and D-051). The CVM statement carries a
declared administration fee, and for one family of classes that figure is not the price the
client pays.

Under RCVM 175 a manager runs one portfolio and sells it through feeder classes, each filing
its own statement. Some houses now file a nominal class-level figure there. In the file, 580
of the 2,655 classes present in both 2024 and 2025 saw their declared fee fall by a factor of
three or more, and 235 of them landed on exactly 0.040%. Some of those had declared 2.60% a
year earlier. Nobody cuts a fee from 2.60% to 0.04%.

So the fee is measured instead. A feeder puts nearly all of its money into one master fund,
which means the two quota series are the same portfolio priced twice, and the only thing
separating them is what the class keeps:

```
fee = 1 - (class growth / master growth) ^ (1 / years)
```

The link between class and master comes from the CVM's portfolio composition file. Nothing
else is needed, and nothing depends on a form being filled in correctly. Checked against an
outside source, the two funds where this mattered most measure 0.396% and 0.511% here,
against 0.37% and 0.42% reported by Economática.

But the measurement is only a coarse signal. Across the whole universe it runs above the
declared fee (median gap +0.27 pt) and is noisy year to year (2024-vs-2025 correlation 0.615),
so the project does not trust its exact value. The fee therefore **does not score a fund**. It
gates the finalists: a fund whose cost — the declared fee, or the measured one where the
declared is suspiciously low — exceeds **1% a year** is struck and the next distinct fund
promoted. See [`docs/04-a-taxa-e-a-conferencia.md`](docs/04-a-taxa-e-a-conferencia.md) and
decision D-051.

Three rules settle the number, and each costs a fund rather than rewards it. Where both
figures exist, the **higher** wins: a class does not charge less than its manager filed, so a
lower measurement is noise rather than a discount. A class that invests through other funds
and **could not** be measured is left with no fee, and drops out through the rule that
already refuses to rank what cannot be priced. Everything else keeps what it filed, because
the problem belongs to one family of classes and not to the market.

Both figures are published side by side, so a reader can see the gap.

## One portfolio, one slot

A manager will often run a single portfolio and sell it through several distribution
wrappers. Caixa offers a dozen of them over one fixed-income portfolio. Each wrapper is a
separate class, each one is eligible, and each earns nearly the same score. A top five
holding two of them gives the client four exposures without saying so.

Two funds count as one when the same manager runs both and the annualised volatility of the
difference between their daily returns is close to zero. Two wrappers of one portfolio differ
only by their fee, which is a constant drag and adds no variance.

Correlation cannot do this job here, which is why the project does not use it. Every
post-fixed fund follows the same overnight curve and correlates above 0.99 with every other
one, so a threshold high enough to catch a genuine twin also marks half of this universe as
duplicated.

When a fund is skipped, it is published beside the list, by name, together with the fund it
repeats and the distance between the two.

## Does it work?

The full test is in [`saida/validacao.md`](saida/validacao.md).

The ranking was rebuilt as of 31 March, 30 June and 30 September 2025, using nothing that was
published after each of those dates. The funds it chose were then measured to the end of the
year against three things: the median of the eligible universe, the CDI, and 1,000 random
five-fund portfolios drawn from that same universe.

| Profile | Beat 1,000 random five-fund portfolios on | Edge over the median |
| --- | --- | --- |
| Emergency reserve | 3 of 3 dates (p90, p98, p97) | +11 to +26 bp |
| Two years or more | 3 of 3 dates (p88, p95, p93) | +8 to +22 bp |

**The verdict passes.** 
The top five beat the median of its universe in all six cuts, by margins between eight and twenty-six basis points.
Post-fixed funds all return close to the CDI, so the whole
distribution is only a few dozen basis points wide, and three cuts inside a single year
cannot separate method from luck. Outcomes are read from the full validated panel rather than
from the funds still eligible at the end, so a fund that shrank out of the universe is still
carried into the average with whatever it did.

These numbers improved when the fee stopped being read off a form and started being measured.

## Development

```bash
uv run pytest                     # 325 tests
uv run pytest -m trap             # the CVM data-trap regressions
uv run pytest -m invariant        # the financial invariants
uv run ruff check . && uv run mypy src
```

No test touches the network. `tests/fixtures/` holds a frozen slice of real CVM data.

Most of the tests check a component against a fixture, which is what catches a wrong formula.
`tests/integration/test_published_output.py` does something different: it opens the delivered
`ranking.json` and asserts against the product. It checks that the window is as long as its
label claims, that no list holds one portfolio twice, that every weight does something, and
that no published field is a placeholder. None of those failures break a function, so a suite
that only looks inward stays green through all of them.

Every push runs lint, types, the test suite and a Docker build on a blank runner.

## Running this on a schedule

[`weekly-ranking.yml`](.github/workflows/weekly-ranking.yml) runs the whole pipeline against
live data and commits a fresh ranking into `saida/`, with nobody watching. Commit `76102a4`
in this repository was written that way, by `github-actions[bot]` rather than by a person.

The scheduled trigger is currently commented out. `saida/` holds the delivered ranking for
31 December 2025, which was checked by hand, and a weekly run would overwrite it with numbers
nobody had looked at yet. The manual trigger still works, so the workflow can be started on
demand from the Actions tab. Uncommenting two lines brings the schedule back.

Turning this into a real routine inside a firm would take four changes, none of them large:

1. **Let the reference date move.** The workflow currently pins 31 December 2025 so that
   every run is comparable. A production routine would compute the date instead, usually the
   last business day of the previous month. The pipeline already accepts any date and is
   point-in-time throughout, so this is one line.
2. **Check that the data is fresh, not only that it is consistent.** The quality report
   answers whether the numbers hang together. It does not answer whether they are recent. If
   the CVM stopped publishing, the pipeline would rank stale data and the funnel would still
   pass. The run should fail when the most recent quota sits further from the reference date
   than a handful of business days.
3. **Write the outputs somewhere versioned.** Committing to git works well for one answer a
   week and stops working when the cadence is daily and several teams read it. An object
   store keyed by reference date, with the run's manifest beside it, keeps every past answer
   reproducible instead of buried in history.
4. **Say what changed, not only that it ran.** The commit message is currently the run date.
   Deriving it from `ranking.json`, naming the funds that entered and left, would turn the
   history into a log of how the ranking moved rather than a list of identical entries.

The pipeline itself would not change for any of this. It is already a single function that
takes a date, and everything above is about what surrounds it.

## Data sources

Everything is public and none of it needs credentials. What was deliberately left out, and
why, is recorded in [`configs/sources.yaml`](configs/sources.yaml).

| Source | Provides |
| --- | --- |
| CVM daily report | quota, net assets, shareholders, subscriptions, redemptions |
| CVM registry (RCVM 175) | classification, target investor, open or closed, exclusive |
| CVM statement and factsheet | admin fee, redemption terms, minimum investment |
| CVM portfolio composition (CDA) | which fund each class holds, which is what makes the fee measurable |
| CVM monthly investor profile | the shareholder base of each class by kind of holder, which is what says whether an individual is inside |
| Central Bank series 12 | daily CDI |
| ANBIMA | the fund classification that defines peer groups, which arrives inside the CVM registry |

## Reading the project

| Document | Contains |
| --- | --- |
| [`docs/01-solution-design.md`](docs/01-solution-design.md) | the design, in Portuguese |
| [`docs/decisoes.md`](docs/decisoes.md) | every decision taken, including the ones later reversed |
| [`docs/04-a-taxa-e-a-conferencia.md`](docs/04-a-taxa-e-a-conferencia.md) | why the declared fee is not the price the client pays, and the ranking checked against outside sources |
| [`docs/02-checklist.md`](docs/02-checklist.md) | what was done, and what was deliberately not |
| `CLAUDE.md` | the working agreement: rules, the thirteen data traps, the quality baseline |

The decision log is the one worth reading. It records what was measured before each choice
and what turned out to be wrong, including a guardrail that missed a 2% error because the
error fitted inside its tolerance, and a first ranking that came back full of institutional
funds because a filter had been written too loosely.

## What this does not do

- **It does not look inside the portfolios.** It measures outcomes rather than holdings, so
  two funds with the same return and risk look identical to it even if one holds Treasury
  paper and the other holds private credit. The composition file is read only to find the
  fund behind each class, never for what that fund owns, and reading it properly is the first
  item of future work.
- **It can only measure the fee of a class that wraps a single fund.** A fund holding assets
  directly has nothing to be compared against and keeps its declared figure, which is correct
  for most of the market but unverified. A class that wraps a fund but also holds cash gives
  a measurement that is a ceiling rather than an exact fee.
- **It cannot see funds that closed.** It measures the past, in a single interest-rate
  regime, and the universe is optimistic by construction.
- **It compares inflation-linked funds against the CDI**, because ANBIMA publishes the IMA as
  a snapshot of the current day rather than as a history. This affects 8% of the universe.
- **It counts the fee twice on purpose.** Once inside the net quota, and once as the heaviest
  weight, because the second counting is the one that says something about next year.
- **It reports before income tax.** Most funds follow the same regressive table and their
  relative order holds. Funds built on incentivised infrastructure debt are exempt for
  individuals, so every fund publishes its tax regime.
- **It evaluates each fund on its own** rather than as part of a portfolio, beyond refusing
  to hold the same portfolio twice.
