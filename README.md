# Brazilian Fixed-Income Fund Ranking

Ranks Brazilian fixed-income funds and returns the top five for each retail client
profile, from public CVM and ANBIMA data, for any reference date.

Built for a case study with a reference period of **31 December 2025**.

## Quick start

```bash
uv sync
uv run ranking --reference-date 2025-12-31
```

One command, about 40 seconds from a cold cache. Downloads roughly 280 MB from the CVM
and the Central Bank, validates 6.3 million rows, and writes to [`saida/`](saida):

| File | For | Contains |
|---|---|---|
| [`ranking.md`](saida/ranking.md) | a person | the two top-five lists, why each fund is there, and what the method cannot see |
| [`ranking.json`](saida/ranking.json) | another system | the same, plus every metric, percentile and source hash |
| [`ranking.html`](saida/ranking.html) | a person, at a glance | the same lists as a self-contained page |
| [`relatorio_qualidade.md`](saida/relatorio_qualidade.md) | whoever needs to trust the numbers | the eligibility funnel against its expected baseline |
| [`validacao.md`](saida/validacao.md) | whoever needs to trust the method | the out-of-sample test |

Those files are committed. A deliverable that only exists after someone runs the pipeline
is not delivered, so the repository carries the answer and the means to rebuild it.

Add `--validate` to rebuild the ranking as of each frozen cut date and measure what
followed. It takes minutes rather than seconds, because it runs the whole pipeline four
times:

```bash
uv run ranking --reference-date 2025-12-31 --validate
```

Or without installing anything but Docker:

```bash
docker build -t fixed-income-ranking .
docker run --rm -v "$PWD/saida:/app/saida" fixed-income-ranking --reference-date 2025-12-31
```

## What it does

Given a reference date, the pipeline:

1. **downloads** the CVM daily fund reports, registry, statements and factsheets, plus the
   Central Bank's CDI series — with retries, a per-host circuit breaker, and a check that
   the payload is really the file it claims to be, because the CVM serves error pages with
   HTTP 200;
2. **validates** every row against a declared schema, sending failures to quarantine *with a
   written reason* and stopping the run outright if more than 5% is unusable;
3. **selects** the funds a retail investor can actually buy — 36,594 registered classes
   become 580 — and compares the count at each step against a baseline measured in advance;
4. **measures** ten return, risk, cost and liquidity figures per fund over a window that is
   exactly as long as its label says, from the daily quota, which already comes net of fees;
5. **ranks** each fund against funds *like it*, weighted per profile, moving any weight
   whose criterion the eligible pool ties on to the criteria that still discriminate;
6. **picks five funds rather than five scores**, passing over any fund that repeats a
   portfolio already on the list;
7. **tests whether the answer holds** by rebuilding the ranking a thousand times.

Every number that decides anything lives in [`configs/`](configs), not in code.

## The two profiles

The split is by **when the client needs the money back**, because 58% of the retail universe
redeems same-day and a single list would hand the same five funds to someone saving for a
holiday and someone saving for three years.

| | Emergency reserve | Two years or more |
|---|---|---|
| Redemption | up to D+1 | up to D+30 |
| Minimum investment | ≤ R$ 5,000 | ≤ R$ 50,000 |
| Eligible funds | 218 | 390 |
| Heaviest weight | admin fee | admin fee |
| Then | volatility, worst fall | excess over CDI, return per unit of risk |

Cost outweighs past return in both. The fee is the only number known with certainty about
next year, and only 40% of funds beat the CDI in 2025.

Weights are declared per profile and the ones actually applied are published beside them.
The liquidity profile admits only funds that pay out within a day, so by the time its funds
are scored, 214 of its 218 settle same-day: redemption speed has done its work as a filter
and has nothing left to say as a criterion. Its weight moves to the criteria that can still
separate funds, and `ranking.json` names it.

## One portfolio, one slot

A manager routinely runs a single portfolio and sells it through a row of distribution
wrappers — Caixa offers a dozen over one fixed-income portfolio. Each is a separate class
in the CVM registry, each is eligible, and each earns nearly the same score. A top five
holding two of them offers four exposures and does not say so.

Two funds count as one when the same manager runs both **and** the difference between their
daily returns barely moves — measured as the annualised volatility of that difference. Two
wrappers of one portfolio differ only by their fee, which is a constant drag and contributes
no variance. Correlation cannot do this job here and is deliberately not used: every
post-fixed fund tracks the same overnight curve and correlates above 0.99 with every other,
so any threshold high enough to catch a twin also marks half the universe as duplicated.

A fund passed over is published beside the list, named, with the fund it repeats and the
distance between them.

## Two scores per fund

A percentile inside an ANBIMA category asks whether a fund is good *for what it is*, which
is what keeps the ranking from simply handing back whoever took the most credit risk. It is
also silent about the category: being first of eighteen scores the same in a strong group
and a weak one.

So every fund carries both — its score against its peers, and the same score recomputed
against the whole eligible pool. When the two diverge, the fund is the best of a group that
is not good, and the reader is entitled to know that before buying.

## Does it work?

Measured, not asserted. See [`saida/validacao.md`](saida/validacao.md).

The ranking was rebuilt as of 31 March, 30 June and 30 September 2025, using nothing
published after each date, and the chosen funds were measured to the end of the year against
the median of the eligible universe, against the CDI, and against **1,000 random five-fund
portfolios drawn from that same universe**. The success criterion was written into
`configs/profiles.yaml` and committed before the test ever ran.

| Profile | Beat chance on | Edge over the median |
|---|---|---|
| Emergency reserve | 2 of 3 dates (p68, p99, p22) | −15 to +21 bp |
| Two years or more | 3 of 3 dates (p71, p94, p72) | −4 to +21 bp |

**The verdict passes and the result is modest.** Read the three qualifications with it:

- The top five beat the median of its universe in **two of six** cuts, and trailed it in the
  other four, by margins between four and fifteen basis points.
- It **underperformed the CDI in all six**, which is unsurprising where only 40% of funds
  beat the CDI over the year, and is the comparison a client makes from memory.
- Measurements are read from the full validated panel, not from the funds still eligible at
  the end. A fund chosen in March that had shrunk out of the universe by December is carried
  into the average with whatever it did. Reading outcomes from the survivors is the
  survivorship bias the test exists to detect, and it moves the numbers.

A high percentile against a narrow distribution is not a large gain. Post-fixed funds all
return close to CDI, so beating almost everyone means beating them by a few dozen basis
points — and losing to almost everyone means the same in reverse. In a market where the
median fee is 0.50% a year, that is the order of magnitude available, and it is small enough
that three cuts inside one year cannot tell method from luck.

`validacao.md` also reports each top five against portfolios drawn from the **cheapest
quarter** of the same universe. Cost leaves the quota before anything is measured, so a
ranking whose heaviest weight is the fee earns part of any advantage by arithmetic that was
knowable before the test was written. That column is reported, not part of the criterion,
which was frozen before it existed.

## Development

```bash
uv run pytest                     # 283 tests
uv run pytest -m trap             # the CVM data-trap regressions
uv run pytest -m invariant        # the financial invariants
uv run ruff check . && uv run mypy src
```

No test touches the network: `tests/fixtures/` holds a frozen slice of real CVM data.

Tests come in two kinds, and the second is the one worth pointing at. Most check a component
against a fixture, which catches a wrong formula. `tests/integration/test_published_output.py`
opens the delivered `ranking.json` and asserts against the product instead — that the window
is as long as its label claims, that no list holds one portfolio twice, that every weight
does something, that no published field is a placeholder. Those failures never break a
function, so a suite that only looks inward stays green through all of them.

Every push runs lint, types, the suite and a Docker build on a blank runner.
[`weekly-ranking.yml`](.github/workflows/weekly-ranking.yml) runs the whole pipeline against
live data every Monday and commits a fresh ranking into `saida/`, unattended.

## Scaling to a daily cadence

Single node, Polars, no orchestrator — the volume does not need one, and the case asks for a
clear path rather than a distributed system. What makes the path real:

- **Parsing happens once.** The daily reports arrive as 280 MB of latin-1, semicolon-
  separated text, and decoding it costs more than the download does. Each monthly file is
  parsed and written back as Parquet under a name carrying the source file's SHA-256, so
  the cache is keyed by the bytes that produced it. The CVM restates by overwriting files in
  place without versioning them; a restated archive hashes differently, misses the cache and
  is parsed again. A cache keyed on the file name would serve stale numbers forever.
- **The panel is assembled by scanning the columnar files**, not by holding a dozen decoded
  frames open at once. That peak, not total volume, is the limit a single node meets first.
- **Point-in-time is enforced in three places**, which is what makes a run for any past date
  a single command — and what made the out-of-sample test cost a day rather than a week.

## Data sources

All public, no credentials.

| Source | Provides |
|---|---|
| CVM daily report | quota, net assets, shareholders, subscriptions, redemptions |
| CVM registry (RCVM 175) | classification, target investor, open/closed, exclusive |
| CVM statement and factsheet | admin fee, redemption terms, minimum investment |
| Central Bank series 12 | daily CDI |
| ANBIMA | the fund classification that defines peer groups, which arrives inside the CVM registry |

Deliberately not used, and why, is documented in [`configs/sources.yaml`](configs/sources.yaml).

## Reading the project

| | |
|---|---|
| [`docs/03-guia-de-defesa.md`](docs/03-guia-de-defesa.md) | the short version: the numbers, the ten questions and their answers |
| [`docs/01-solution-design.md`](docs/01-solution-design.md) | the design, in plain Portuguese |
| [`docs/decisoes.md`](docs/decisoes.md) | every decision taken, including the ones later reversed |
| [`docs/02-checklist.md`](docs/02-checklist.md) | what was done, and what was deliberately not |
| `CLAUDE.md` | the working agreement: rules, the thirteen data traps, the quality baseline |

The decision log is the one worth reading. It records what was measured before each choice,
and what was got wrong — including a guardrail that failed to catch a 2% error because the
error fitted inside its tolerance, and a first ranking that came back holding institutional
funds because a filter had been specified too loosely.

## What this does not do

- **It does not look inside the portfolios.** It measures outcomes, not holdings. This is the
  main gap; the CVM publishes the data (CDA) and it is the first item of future work.
- It measures the past, in one interest-rate regime.
- It cannot see funds that closed, so the universe is optimistic by construction.
- It compares inflation-linked funds against CDI, because ANBIMA publishes the IMA as a
  snapshot of the current day rather than as history. Affects 8% of the universe.
- It counts the fee twice on purpose — once inside the net quota, once as the heaviest
  weight — because the second counting is the one that speaks about next year.
- It reports before income tax. Most funds follow the same regressive table and their
  relative order holds; funds built on incentivised infrastructure debt are exempt for
  individuals and are understated by a gross comparison, so every fund publishes its regime.
- It evaluates each fund on its own rather than as a portfolio, beyond refusing to hold the
  same portfolio twice.

## License

Case study. Not investment advice.
