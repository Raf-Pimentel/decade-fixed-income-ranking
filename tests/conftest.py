"""Shared test fixtures.

Everything here reads from `tests/fixtures/`, which is frozen real CVM data.
No test in this suite touches the network.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# Reference date of the fixture slice: October to December 2025.
FIXTURE_REFERENCE_DATE = dt.date(2025, 12, 31)

# The fund that is in the sample on purpose: its registry `Data_Inicio` says
# 2025-05-12, but it was constituted on 1994-05-26. See CLAUDE.md, trap 3.
AGE_TRAP_CNPJ = "00068305000135"

# Values computed independently from the fixture, outside the implementation,
# so that the tests verify the code against a number the code did not produce.
EXPECTED = {
    AGE_TRAP_CNPJ: {
        "observations": 64,
        "first_quota": 42.4090370000,
        "last_quota": 43.7544400000,
        "period_return": 0.031724441185,
    },
    "42592315000115": {
        "observations": 64,
        "period_return": 0.027386613839,
    },
}
EXPECTED_CDI_COMPOUNDED = 0.035903629100


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def daily_report_path() -> Path:
    return FIXTURES / "daily_report.csv"


@pytest.fixture
def dirty_daily_report_path() -> Path:
    return FIXTURES / "daily_report_dirty.csv"


@pytest.fixture
def registry_class_path() -> Path:
    return FIXTURES / "registry_class.csv"


@pytest.fixture
def registry_fund_path() -> Path:
    return FIXTURES / "registry_fund.csv"


@pytest.fixture
def statement_path() -> Path:
    return FIXTURES / "statement.csv"


@pytest.fixture
def cdi_path() -> Path:
    return FIXTURES / "cdi.json"


@pytest.fixture
def config_dir() -> Path:
    return Path(__file__).parents[1] / "configs"


@pytest.fixture
def reference_date() -> dt.date:
    return FIXTURE_REFERENCE_DATE


# --------------------------------------------------------------------------
# Readers used by tests.
#
# These live here, not in `src`, on purpose: the production modules that do
# maths must stay pure and take plain numbers. Reading a CSV is the test's job.
# --------------------------------------------------------------------------


@pytest.fixture
def quota_series():
    """Return the quota series of one fund from the frozen daily report."""

    def _read(cnpj: str) -> list[float]:
        import csv

        digits = "".join(c for c in cnpj if c.isdigit())
        rows = []
        with open(FIXTURES / "daily_report.csv", encoding="latin-1") as fh:
            for row in csv.DictReader(fh, delimiter=";"):
                if "".join(c for c in row["CNPJ_FUNDO_CLASSE"] if c.isdigit()) == digits:
                    rows.append((row["DT_COMPTC"], float(row["VL_QUOTA"])))
        return [quota for _, quota in sorted(rows)]

    return _read


@pytest.fixture
def cdi_rates() -> list[float]:
    """Daily CDI as a decimal fraction — the file stores percent per day."""
    import json

    with open(FIXTURES / "cdi.json", encoding="utf-8") as fh:
        return [float(day["valor"]) / 100 for day in json.load(fh)]
