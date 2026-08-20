"""Data contracts: nothing crosses a stage boundary without being checked.

The rule is that bad rows are *quarantined with a reason*, never silently
dropped, so that we can look at what was rejected instead of trusting that
everything was fine.
"""

from __future__ import annotations

import datetime as dt

import pytest
from pandera import errors as pa_errors

from ranking.contracts import quality, schemas
from ranking.extract import readers


@pytest.fixture
def dirty(dirty_daily_report_path):
    return readers.read_daily_report(dirty_daily_report_path)


# --------------------------------------------------------------------------
# What the schema must reject
# --------------------------------------------------------------------------


def test_clean_fixture_passes_the_contract(daily_report_path, reference_date) -> None:
    frame = readers.read_daily_report(daily_report_path)
    result = schemas.validate_daily_report(frame, reference_date=reference_date)
    assert result.quarantined.is_empty()
    assert len(result.clean) == 1280


def test_negative_quota_is_quarantined(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    reasons = set(result.quarantined["reason"].to_list())
    assert any("quota" in reason for reason in reasons)


def test_missing_quota_is_quarantined(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    assert not result.clean["valor_cota"].is_null().any()


def test_negative_net_assets_is_quarantined(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    assert (result.clean["patrimonio_liquido"] >= 0).all()


def test_dates_after_the_reference_date_are_dropped(dirty, reference_date) -> None:
    """A ranking dated 2025-12-31 must not see January 2026. Ever."""
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    assert result.clean["data"].max() <= reference_date


def test_duplicate_rows_are_collapsed(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    keys = result.clean.select(["cnpj_classe", "data"])
    assert len(keys.unique()) == len(keys)


def test_every_quarantined_row_carries_a_reason(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    assert not result.quarantined.is_empty()
    assert not result.quarantined["reason"].is_null().any()


def test_nothing_is_lost_between_clean_and_quarantine(dirty, reference_date) -> None:
    """Rows either pass, or are quarantined, or are explicitly dropped as
    future-dated. No row may simply vanish."""
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    accounted = len(result.clean) + len(result.quarantined) + result.dropped_future
    assert accounted + result.deduplicated == len(dirty)


# --------------------------------------------------------------------------
# The 5% brake
# --------------------------------------------------------------------------


def test_pipeline_stops_when_too_much_is_quarantined() -> None:
    """Better to deliver no ranking than a quietly biased one."""
    with pytest.raises(quality.TooMuchQuarantinedError):
        quality.assert_quarantine_within_limit(total_rows=1000, quarantined_rows=51, limit=0.05)


def test_pipeline_continues_below_the_limit() -> None:
    quality.assert_quarantine_within_limit(total_rows=1000, quarantined_rows=49, limit=0.05)


# --------------------------------------------------------------------------
# The funnel is the data regression test
# --------------------------------------------------------------------------


def test_funnel_within_tolerance_passes() -> None:
    report = quality.compare_funnel(
        observed={"fixed_income": 7_700},
        expected={"fixed_income": 7_759},
        tolerance=0.03,
    )
    assert report.ok


def test_funnel_outside_tolerance_fails_loudly() -> None:
    """A broken join that halves the universe is invisible in a code review
    and obvious here."""
    report = quality.compare_funnel(
        observed={"with_fee_and_redemption": 412},
        expected={"with_fee_and_redemption": 1_003},
        tolerance=0.03,
    )
    assert not report.ok
    assert "with_fee_and_redemption" in report.deviations


def test_funnel_report_is_human_readable() -> None:
    report = quality.compare_funnel(
        observed={"fixed_income": 7_759}, expected={"fixed_income": 7_759}, tolerance=0.03
    )
    text = report.to_markdown()
    assert "fixed_income" in text
    assert "7" in text


# --------------------------------------------------------------------------
# The output contract: what another team depends on
# --------------------------------------------------------------------------


def test_output_declares_a_schema_version() -> None:
    payload = schemas.RankingOutput(
        schema_version="1.0.0",
        reference_date=dt.date(2025, 12, 31),
        lookback_months=12,
        sources={},
        profiles=[],
    )
    assert payload.schema_version == "1.0.0"


def test_output_rejects_a_top_list_longer_than_configured() -> None:
    with pytest.raises(ValueError):
        schemas.ProfileRanking(
            profile_id="retail",
            label="Retail",
            eligible_universe_size=871,
            weights={"admin_fee": 25},
            top=[schemas.RankedFund.model_construct() for _ in range(6)],
            top_n=5,
        )


# --------------------------------------------------------------------------
# The second lock: what leaves the stage is checked against the declaration
# --------------------------------------------------------------------------


def test_the_clean_set_satisfies_the_declared_schema(daily_report_path, reference_date) -> None:
    """Triage decides who passes; the schema asserts that whoever passed is
    actually sound. If this ever fails, the fault is in the rules, not the data."""
    frame = readers.read_daily_report(daily_report_path)
    result = schemas.validate_daily_report(frame, reference_date=reference_date)
    schemas.assert_matches_contract(result.clean)  # must not raise


def test_the_clean_set_from_dirty_input_also_satisfies_it(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    schemas.assert_matches_contract(result.clean)


def test_the_declared_schema_would_catch_a_bad_row(reference_date) -> None:
    """Proof the second lock is closed, not just present."""
    import datetime as dt

    import polars as pl

    smuggled = pl.DataFrame(
        {
            "cnpj_classe": ["00017024000153"],
            "data": [dt.date(2025, 12, 1)],
            "valor_cota": [-1.0],
            "patrimonio_liquido": [1.0],
            "cotistas": [1],
        }
    )
    with pytest.raises(pa_errors.SchemaErrors):
        schemas.assert_matches_contract(smuggled)


def test_the_row_count_always_adds_up(dirty, reference_date) -> None:
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    assert result.received == len(dirty)


def test_the_quarantine_share_is_reported(dirty, reference_date) -> None:
    """The pipeline needs this number to decide whether to carry on."""
    result = schemas.validate_daily_report(dirty, reference_date=reference_date)
    assert 0.0 < result.quarantined_share < 1.0
