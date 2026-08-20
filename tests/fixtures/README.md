# Test fixtures

Real slices of CVM data, frozen in the repository. **No test ever hits the network** —
a test that depends on the internet is not a test, it is a bet.

## Provenance

Extracted on 2026-08-20 from the production CVM files, reference period
**October to December 2025** (three contiguous months, ~62 business days).

| File | Content | Source |
|---|---|---|
| `daily_report.csv` | 20 funds × 64 days of quota, net assets, shareholders | `inf_diario_fi_2025{10,11,12}.zip` |
| `registry_class.csv` | registry rows for those 20 classes | `registro_fundo_classe.zip` → `registro_classe.csv` |
| `registry_fund.csv` | the parent funds of those classes | same zip → `registro_fundo.csv` |
| `statement.csv` | fees, redemption terms, minimum investment | `extrato_fi_2025.csv` |
| `cdi.json` | daily CDI, Oct–Dec 2025 | Central Bank, series 12 |
| `daily_report_dirty.csv` | **hand-written**, see below | — |

The 20 funds were chosen to span **9 different ANBIMA groups** and all three target-investor
categories (17 retail, 1 qualified, 2 professional), so that peer-group logic and
profile eligibility are both exercised.

## The one fund that is there on purpose

`00068305000135` is in the sample because it is the **age trap** (trap 3 in `CLAUDE.md`):
its registry `Data_Inicio` says 2025-05-12, but the fund was constituted on **1994-05-26**.
Any code that reads fund age from the wrong field will fail the regression test.

## `daily_report_dirty.csv`

Hand-written, one defect per row, so each validation rule has something to catch:

| Row | Defect | Expected handling |
|---|---|---|
| 1 | CNPJ formatted `00.017.024/0001-53` | normalised to 14 digits, kept |
| 3 | exact duplicate of row 2 | de-duplicated, last one wins |
| 4 | negative quota | quarantined |
| 5 | empty quota | quarantined |
| 6 | date `2026-01-15`, after the reference date | dropped as future |
| 7 | CNPJ `123` — too short | quarantined |
| 8 | CNPJ `00017024000199` — bad check digit | quarantined |
| 9 | `ID_SUBCLASSE` filled in | excluded: subclass rows duplicate the series |
| 11 | quota jumps +50% in one day | **flagged, not dropped** — may be a legitimate amortisation |
| 12 | negative net assets | quarantined |

Rows 10–12 also share a CNPJ with a very short series, which must fail the
minimum-observations rule.

## Regenerating

These files are committed on purpose and should not be regenerated casually — the
expected values in the tests are tied to them. If the CVM restates the period, the
fixtures stay as they are: their job is to keep the code stable, not to track the source.
