"""End-to-end: the pieces work on their own, do they work together?

Runs the whole pipeline against the frozen fixture — 20 funds, one quarter —
with the network disabled. Nothing here is allowed to download anything.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from ranking import pipeline


@pytest.fixture(scope="module")
def run_output(tmp_path_factory):
    """One full run, shared by every test below.

    Module-scoped on purpose. Re-running the whole pipeline for each assertion
    turned a two-second suite into a minute-long one, and a slow suite is a
    suite people stop running.

    Fifty simulations rather than the configured thousand: these tests check
    that the machinery holds together, not that the ranking is stable. The
    full count runs against the real universe.
    """
    output_dir = tmp_path_factory.mktemp("saida")
    fixtures = Path(__file__).parents[1] / "fixtures"
    configs = Path(__file__).parents[2] / "configs"
    return pipeline.run(
        reference_date=dt.date(2025, 12, 31),
        config_dir=configs,
        input_dir=fixtures,
        output_dir=output_dir,
        offline=True,  # never reach the network
        lookback_months=3,  # the fixture only holds one quarter
        simulations=50,
    )


@pytest.fixture
def result(run_output):
    return run_output


@pytest.fixture
def output_dir(run_output):
    return run_output.output_dir


def test_pipeline_produces_both_outputs(result, output_dir) -> None:
    assert (output_dir / "ranking.json").exists()
    assert (output_dir / "ranking.md").exists()


def test_pipeline_produces_a_quality_report(result, output_dir) -> None:
    """Whoever needs to trust the numbers reads this file first."""
    assert (output_dir / "relatorio_qualidade.md").exists()


def test_output_matches_the_declared_contract(result, output_dir) -> None:
    payload = json.loads((output_dir / "ranking.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0.0"
    assert payload["reference_date"] == "2025-12-31"
    assert {p["profile_id"] for p in payload["profiles"]} == {"varejo_liquidez", "varejo_prazo"}


def test_every_ranked_fund_carries_the_numbers_that_justify_it(result, output_dir) -> None:
    """Exposability: another team must be able to see *why*, not just *who*."""
    payload = json.loads((output_dir / "ranking.json").read_text(encoding="utf-8"))
    for profile in payload["profiles"]:
        for fund in profile["top"]:
            assert fund["cnpj_classe"]
            assert fund["metrics"]
            assert "appearance_rate" in fund
            assert fund["rationale"]


def test_sources_are_recorded_for_reproducibility(result, output_dir) -> None:
    payload = json.loads((output_dir / "ranking.json").read_text(encoding="utf-8"))
    assert payload["sources"], "the manifest proves which data produced this ranking"


def test_running_twice_gives_the_same_bytes(fixtures_dir, config_dir, tmp_path) -> None:
    """Idempotence. If this fails, it is a bug, not a feature."""
    first_dir, second_dir = tmp_path / "one", tmp_path / "two"
    for out in (first_dir, second_dir):
        pipeline.run(
            reference_date=dt.date(2025, 12, 31),
            config_dir=config_dir,
            input_dir=fixtures_dir,
            output_dir=out,
            offline=True,
            lookback_months=3,
            simulations=50,
        )
    one = json.loads((first_dir / "ranking.json").read_text(encoding="utf-8"))
    two = json.loads((second_dir / "ranking.json").read_text(encoding="utf-8"))

    # `generated_at` is provenance, not output: it records when the file was
    # written, and it is the only field allowed to differ between two runs of
    # the same reference date. Everything else must be identical.
    assert one.pop("generated_at") != two.pop("generated_at")
    assert one == two


def test_no_data_after_the_reference_date_is_used(result) -> None:
    """Point-in-time, checked at the top level and not only inside the reader.
    If this ever fails, the backtest in Phase 5.5 is worthless."""
    assert result.max_observation_date <= dt.date(2025, 12, 31)


def test_pipeline_is_importable_not_only_a_command() -> None:
    """The case asks that another team can consume this. A CLI-only pipeline
    would not qualify."""
    assert callable(pipeline.run)


def test_offline_run_never_opens_a_connection(
    monkeypatch, fixtures_dir, config_dir, tmp_path
) -> None:
    def explode(*args, **kwargs):  # pragma: no cover - only runs on failure
        raise AssertionError("the pipeline tried to reach the network in offline mode")

    monkeypatch.setattr("httpx.Client.request", explode)
    pipeline.run(
        reference_date=dt.date(2025, 12, 31),
        config_dir=config_dir,
        input_dir=fixtures_dir,
        output_dir=tmp_path,
        offline=True,
        lookback_months=3,
        simulations=50,
    )
