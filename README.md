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
and the Central Bank, validates 6.3 million rows, and writes five files to `saida/`:

| File | For | Contains |
|---|---|---|
| `ranking.html` | a person, at a glance | the same lists as a self-contained page, regenerated on every run |
| `ranking.md` | a person | the two top-five lists, why each fund is there, and what the method cannot see |
| `ranking.json` | another system | the same, plus every metric, percentile and source hash |
| `relatorio_qualidade.md` | whoever needs to trust the numbers | the eligibility funnel against its expected baseline |
| `validacao.md` | whoever needs to trust the method | the out-of-sample test |

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
4. **measures** ten return, risk, cost and liquidity figures per fund from the daily quota,
   which already comes net of fees;
5. **ranks** each fund against funds *like it*, weighted differently per profile;
6. **tests whether the answer holds** by rebuilding the ranking a thousand times.

Every number that decides anything lives in [`configs/`](configs), not in code.

## The two profiles

The split is by **when the client needs the money back**, because 58% of the retail universe
redeems same-day and a single list would hand the same five funds to someone saving for a
holiday and someone saving for three years.

| | Emergency reserve | Two years or more |
|---|---|---|
| Redemption | up to D+1 | up to D+30 |
| Minimum investment | ≤ R$ 5,000 | ≤ R$ 50,000 |
| Heaviest weight | admin fee (30) | admin fee (25) |
| Then | volatility, worst fall | excess over CDI, return per unit of risk |

Cost outweighs past return in both. The fee is the only number known with certainty about
next year, and only 40% of funds beat the CDI in 2025.

## Does it work?

Yes, modestly — and that is measured, not asserted. See [`saida/validacao.md`](saida).

The ranking was rebuilt as of 31 March, 30 June and 30 September 2025, using nothing
published after each date, and the chosen funds were measured to the end of the year against
the median of the eligible universe and against **1,000 random five-fund portfolios drawn
from that same universe**.

| Profile | Beat chance on | Edge over the median |
|---|---|---|
| Emergency reserve | 3 of 3 dates (p92, p100, p98) | +10 to +31 bp |
| Two years or more | 2 of 3 dates (p84, p97, p51) | −8 to +20 bp |

The success criterion was written into `configs/profiles.yaml` and committed before the test
ever ran. A high percentile against a narrow distribution is not a large gain: post-fixed
funds all return close to CDI, so beating almost everyone means beating them by a few dozen
basis points. In a market where the median fee is 0.50% a year, that is the order of
magnitude available.

## Development

```bash
uv run pytest                     # 223 tests
uv run pytest -m trap             # the CVM data-trap regressions
uv run pytest -m invariant        # the financial invariants
uv run ruff check . && uv run mypy src
```

No test touches the network: `tests/fixtures/` holds a frozen slice of real CVM data.

Every push runs lint, types, the suite and a Docker build on a blank runner.
[`weekly-ranking.yml`](.github/workflows/weekly-ranking.yml) runs the whole pipeline against
live data every Monday and publishes a fresh ranking, unattended.

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
| [`docs/decisoes.md`](docs/decisoes.md) | every decision taken, including the six that were later reversed |
| [`docs/02-checklist.md`](docs/02-checklist.md) | what was done, and what was deliberately not |
| `CLAUDE.md` | the working agreement: rules, the twelve data traps, the quality baseline |

The decision log is the one worth reading. It records what was measured before each choice,
and what was got wrong — including a guardrail that failed to catch a 2% error because the
error fitted inside its tolerance, and a first ranking that came back holding institutional
funds because a filter had been specified too loosely.

## What this does not do

- **It does not look inside the portfolios.** It measures outcomes, not holdings. This is the
  main gap; the CVM publishes the data (CDA) and it is the first item of future work.
- It measures the past, in one interest-rate regime.
- It cannot see funds that closed, so the universe is optimistic by construction.
- It compares inflation-linked funds against CDI, because ANBIMA does not publish the IMA
  history in a usable format. Affects 8% of the universe.
- It ignores income tax, and evaluates each fund on its own rather than as a portfolio.

## License

Case study. Not investment advice.
