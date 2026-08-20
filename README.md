# Brazilian Fixed-Income Fund Ranking

Ranks Brazilian fixed-income funds and returns the top 5 for each client profile,
from public CVM and ANBIMA data, for a given reference date.

> **Status: under construction — phase 2 of 6.**
> The test suite is deliberately **red**: it was written before the code, and the
> modules it imports do not exist yet. CI will stay red until phase 5 closes.
> That is the intended state of a test-first build, not a broken build.
>
> The design document is [`docs/01-solution-design.md`](docs/01-solution-design.md)
> (in Portuguese), and every decision taken — including the four that were later
> reversed — is logged in [`docs/decisoes.md`](docs/decisoes.md).

## What it does

Given a reference date, the pipeline downloads the CVM daily fund reports, keeps the
funds a real client can actually buy, computes ten return, risk, cost and liquidity
figures for each one, compares every fund only against similar funds, and applies a
different set of weights per client profile.

Before publishing, it re-runs the whole ranking a thousand times — resampling the
returns and varying the weights — and reports **how often each fund stayed in the top 5**.
The output is not "the single best fund"; it is "these five hold up, and the order
between them is not meaningful".

## Quick start

```bash
uv sync
uv run ranking --reference-date 2025-12-31
```

Outputs land in `saida/`:

| File | For |
|---|---|
| `ranking.json` | another system |
| `ranking.md` | a person |
| `relatorio_qualidade.md` | whoever needs to trust the data |

Or without installing anything but Docker:

```bash
docker build -t fixed-income-ranking .
docker run --rm -v "$PWD/saida:/app/saida" fixed-income-ranking --reference-date 2025-12-31
```

## Development

```bash
uv run pytest                     # tests
uv run pytest --cov=src/ranking   # with coverage
uv run pytest -m trap             # only the CVM data-trap regressions
uv run pytest -m invariant        # only the financial invariants
uv run ruff check . && uv run mypy src
```

Every push runs lint, type checks, the suite and a Docker build on a blank
runner — which is what actually backs the "reproducible from a clean
environment" claim.

## Running it unattended

[`.github/workflows/weekly-ranking.yml`](.github/workflows/weekly-ranking.yml)
runs the whole pipeline from scratch against live CVM data and publishes a fresh
ranking, with nobody watching. The schedule is switched on once the pipeline is
complete; until then the workflow can be triggered by hand.

## Data sources

All public, no credentials required. Declared in [`configs/sources.yaml`](configs/sources.yaml).

| Source | Provides |
|---|---|
| CVM daily report | quota value, net assets, shareholders, subscriptions, redemptions |
| CVM registry | name, manager, classification, target investor |
| CVM statement / factsheet | admin fee, redemption terms, minimum investment |
| Central Bank series 12 | daily CDI rate |
| ANBIMA IMA indices | IMA-B and IRF-M, to benchmark inflation-linked and fixed-rate funds |

## Configuration

Nothing that matters is hard-coded. Three files decide everything:

| File | Decides |
|---|---|
| [`configs/universe.yaml`](configs/universe.yaml) | which funds compete |
| [`configs/profiles.yaml`](configs/profiles.yaml) | what "best" means, per profile |
| [`configs/sources.yaml`](configs/sources.yaml) | where the data comes from |

## License

Case study, not for production use.
