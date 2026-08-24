# Brazilian Fixed-Income Fund Ranking

[![CI](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/ci.yml/badge.svg)](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/ci.yml)
[![Weekly ranking](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/weekly-ranking.yml/badge.svg)](https://github.com/Raf-Pimentel/decade-fixed-income-ranking/actions/workflows/weekly-ranking.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

This project ranks Brazilian fixed-income funds and returns the top five for each retail
client profile, using public data from the CVM and the Central Bank. It works for any
reference date.

It was built for a case study with a reference period of **31 December 2025**.

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

Those files are committed to the repository. A deliverable that only exists after someone
runs the pipeline has not really been delivered.

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
   classes down to 580, and checks the count at each step against a baseline measured in
   advance;
4. **measures** return, risk, cost and liquidity for each fund over a window that is exactly
   as long as its label says, using the daily quota, which already comes net of fees;
5. **ranks** each fund against funds like it, weighted by profile. If a criterion turns out
   to be a tie across the whole eligible pool, its weight moves to the criteria that can
   still tell funds apart;
6. **picks five funds rather than five scores**, skipping any fund that repeats a portfolio
   already on the list;
7. **checks whether the answer holds** by rebuilding the ranking a thousand times.

Every number that decides anything lives in [`configs/`](configs) rather than in the code.
The design is written up in [`docs/01-solution-design.md`](docs/01-solution-design.md).

## The two profiles

The split is by when the client needs the money back. 58% of the retail universe pays out the
same day, and a single list would hand the same five funds to someone saving for a holiday
and someone saving for three years.

| | Emergency reserve | Two years or more |
| --- | --- | --- |
| Redemption | up to D+1 | up to D+30 |
| Minimum investment | ≤ R$ 5,000 | ≤ R$ 50,000 |
| Eligible funds | 218 | 390 |
| Heaviest weight | admin fee | admin fee |
| Then | volatility, worst fall | excess over CDI, return per unit of risk |

Cost outweighs past return in both profiles. The fee is the only number we know with
certainty about next year, and only 40% of funds beat the CDI in 2025.

The weights are a declared choice rather than something derived, and the ones actually
applied are published next to the ones declared. A criterion that every eligible fund ties on
cannot separate anything, so its weight moves to the criteria that still can, and
`ranking.json` says which criterion this happened to.

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
| Emergency reserve | 2 of 3 dates (p68, p99, p22) | −15 to +21 bp |
| Two years or more | 3 of 3 dates (p71, p94, p72) | −4 to +21 bp |

**The verdict passes and the result is modest.** The top five beat the median of its universe
in two of six cuts and trailed it in the other four, and it underperformed the CDI in all
six. Post-fixed funds all return close to the CDI, so the whole distribution is only a few
dozen basis points wide, and three cuts inside a single year cannot separate method from
luck. Outcomes are read from the full validated panel rather than from the funds still
eligible at the end, so a fund that shrank out of the universe is still carried into the
average with whatever it did.

## Development

```bash
uv run pytest                     # 288 tests
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
| Central Bank series 12 | daily CDI |
| ANBIMA | the fund classification that defines peer groups, which arrives inside the CVM registry |

## Reading the project

| Document | Contains |
| --- | --- |
| [`docs/03-guia-de-defesa.md`](docs/03-guia-de-defesa.md) | the short version: the numbers, ten questions and their answers |
| [`docs/01-solution-design.md`](docs/01-solution-design.md) | the design, in Portuguese |
| [`docs/decisoes.md`](docs/decisoes.md) | every decision taken, including the ones later reversed |
| [`docs/02-checklist.md`](docs/02-checklist.md) | what was done, and what was deliberately not |
| `CLAUDE.md` | the working agreement: rules, the thirteen data traps, the quality baseline |

The decision log is the one worth reading. It records what was measured before each choice
and what turned out to be wrong, including a guardrail that missed a 2% error because the
error fitted inside its tolerance, and a first ranking that came back full of institutional
funds because a filter had been written too loosely.

## What this does not do

- **It does not look inside the portfolios.** It measures outcomes rather than holdings, so
  two funds with the same return and risk look identical to it even if one holds Treasury
  paper and the other holds private credit. The CVM publishes this data (CDA) and it is the
  first item of future work.
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
