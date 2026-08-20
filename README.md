# Brazilian Fixed-Income Fund Ranking

Ranks Brazilian fixed-income funds and returns the top 5 for each client profile,
from public CVM and ANBIMA data, for a given reference date.

> **Status: under construction.** Phase 2 of 6 — project skeleton and test suite.
> The design document is [`docs/01-solution-design.md`](docs/01-solution-design.md)
> (in Portuguese), and every decision taken is logged in
> [`docs/decisoes.md`](docs/decisoes.md).

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

## Development

```bash
uv run pytest                     # tests
uv run pytest --cov=src           # with coverage
uv run ruff check . && uv run mypy src
```

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
