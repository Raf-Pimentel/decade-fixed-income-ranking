"""Regression tests for the eight CVM data traps listed in CLAUDE.md.

Each of these cost real investigation in Phase 1. They are the tests most
likely to save the project, because every one of them fails *silently* in
production: the pipeline runs, produces numbers, and the numbers are wrong.
"""

from __future__ import annotations

import csv
import datetime as dt

import pytest

from ranking import config
from ranking.contracts import rules
from ranking.extract import manifest, readers
from ranking.transform import normalize

pytestmark = pytest.mark.trap


# --------------------------------------------------------------------------
# Trap 1 — the daily report is per CLASS, not per fund, since 2024-01
# --------------------------------------------------------------------------


def test_daily_report_is_read_at_class_grain(daily_report_path) -> None:
    """Code written for the pre-2024 layout joins on the wrong key and raises
    nothing at all. The reader must demand the class columns."""
    frame = readers.read_daily_report(daily_report_path)
    assert "cnpj_classe" in frame.columns
    assert "cnpj_fundo" not in frame.columns


def test_reader_refuses_the_old_layout(tmp_path) -> None:
    old = tmp_path / "old_layout.csv"
    old.write_text(
        "TP_FUNDO;CNPJ_FUNDO;DT_COMPTC;VL_QUOTA\nFI;00.017.024/0001-53;2025-12-01;41.25\n",
        encoding="latin-1",
    )
    with pytest.raises(readers.UnsupportedLayoutError):
        readers.read_daily_report(old)


# --------------------------------------------------------------------------
# Trap 2 — cad_fi.csv is obsolete: 10.3% coverage, 0% of fees filled in
# --------------------------------------------------------------------------


def test_cad_fi_is_not_declared_as_a_fee_source(config_dir) -> None:
    sources = config.load_sources(config_dir / "sources.yaml")
    declared = " ".join(str(source.url) for source in sources.values()).lower()
    assert "cad_fi.csv" not in declared, (
        "cad_fi.csv covers 10.3% of fixed-income classes and has no fees. "
        "Fees come from EXTRATO and LAMINA. See decision D-002."
    )


# --------------------------------------------------------------------------
# Trap 3 — `Data_Inicio` is the RCVM 175 adaptation date, not the fund's age
# --------------------------------------------------------------------------


def test_fund_age_does_not_come_from_registry_start_date(
    registry_class_path, registry_fund_path
) -> None:
    """CNPJ 00068305000135 says 2025-05-12 in the registry but was constituted
    in 1994. Reading the wrong field would call a 31-year-old fund a newborn
    and drop two thirds of the universe."""
    frame = readers.read_registry(registry_class_path, registry_fund_path)
    row = frame.filter(frame["cnpj_classe"] == "00068305000135").to_dicts()[0]

    age = normalize.fund_age_years(row, as_of=dt.date(2025, 12, 31))

    assert age > 30, f"expected a fund older than 30 years, got {age:.1f}"


def test_registry_start_date_equals_the_rcvm175_adaptation_date(registry_class_path) -> None:
    """Documents *why* the field is unusable, straight from the frozen data."""
    with open(registry_class_path, encoding="latin-1") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter=";")]

    matching = [r for r in rows if r["Data_Inicio"] and r.get("Data_Inicio")]
    assert matching, "fixture should contain rows with a start date"
    # Every one of them is an adaptation date, i.e. 2024 or later.
    assert all(r["Data_Inicio"][:4] >= "2024" for r in matching)


# --------------------------------------------------------------------------
# Trap 4 — CNPJ arrives in two different formats
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    ["00.017.024/0001-53", "00017024000153", " 00017024000153 ", "00.017.024/0001-53\n"],
)
def test_cnpj_formats_all_normalise_to_the_same_key(raw: str) -> None:
    assert normalize.cnpj(raw) == "00017024000153"


def test_cnpj_with_bad_check_digit_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize.cnpj("00017024000199")


def test_cnpj_too_short_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize.cnpj("123")


# --------------------------------------------------------------------------
# Trap 5 — subclass rows duplicate the series
# --------------------------------------------------------------------------


def test_subclass_rows_are_excluded(dirty_daily_report_path) -> None:
    """The dirty fixture holds one subclass row for 00068305000135 on
    2025-12-01, alongside the class-level row for the same day. Keeping both
    would double-count that fund."""
    frame = readers.read_daily_report(dirty_daily_report_path)
    same_day = frame.filter(
        (frame["cnpj_classe"] == "00068305000135") & (frame["data"] == dt.date(2025, 12, 1))
    )
    assert len(same_day) == 1
    assert same_day.to_dicts()[0]["valor_cota"] == pytest.approx(12.3456789)


# --------------------------------------------------------------------------
# Trap 6 — the CVM overwrites files on restatement, with no versioning
# --------------------------------------------------------------------------


def test_manifest_records_a_hash_for_every_file(tmp_path) -> None:
    payload = tmp_path / "inf_diario_fi_202512.zip"
    payload.write_bytes(b"not really a zip, but it hashes just fine")

    entry = manifest.record(payload)

    assert entry.sha256 and len(entry.sha256) == 64
    assert entry.size_bytes == payload.stat().st_size
    assert entry.downloaded_at is not None


def test_manifest_detects_a_changed_file(tmp_path) -> None:
    """This is the whole point: proving which version of the data produced a
    given ranking, months later."""
    payload = tmp_path / "extrato_fi_2025.csv"
    payload.write_bytes(b"original")
    before = manifest.record(payload)

    payload.write_bytes(b"restated by the CVM")
    after = manifest.record(payload)

    assert before.sha256 != after.sha256


# --------------------------------------------------------------------------
# Trap 7 — files are latin-1 with a semicolon separator
# --------------------------------------------------------------------------


def test_accented_names_survive_the_read(registry_class_path) -> None:
    """Reading latin-1 as UTF-8 either explodes or mangles every fund name
    that contains an accent — and most Brazilian fund names do."""
    frame = readers.read_registry_classes(registry_class_path)
    names = " ".join(frame["denominacao_social"].to_list())
    assert "Ã" not in names and "Ã§" not in names, "mojibake: wrong encoding"


# --------------------------------------------------------------------------
# Trap 8 — a large daily move may be a legitimate amortisation
# --------------------------------------------------------------------------


def test_large_daily_move_is_flagged_not_dropped(dirty_daily_report_path) -> None:
    """Dropping the row would turn a real corporate action into a data gap.
    Flagging keeps the series intact and lets a human decide."""
    frame = readers.read_daily_report(dirty_daily_report_path)
    checked = rules.flag_implausible_moves(frame, threshold=0.20)

    flagged = checked.filter(checked["implausible_move"])
    assert len(flagged) >= 1
    # nothing was removed
    assert len(checked) == len(frame)
