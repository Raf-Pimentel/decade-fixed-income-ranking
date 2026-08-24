"""Loading and validating the three configuration files.

Nothing that decides the ranking lives in code, so these loaders are the point
where a typo in YAML becomes a loud error instead of a silently different
ranking. Every model forbids unknown keys for exactly that reason: a misspelled
`min_shareolders` would otherwise be ignored and the filter would never run.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# universe.yaml: which funds compete
# ---------------------------------------------------------------------------


class Filters(_Strict):
    classification: list[str]
    status: list[str]
    condominium: list[str]
    exclude_exclusive: bool
    min_net_assets_brl: float
    min_shareholders: int
    min_observations: int
    require_fee_and_redemption: bool


class Fees(_Strict):
    """How much of a class must sit in one fund before its fee can be measured."""

    min_master_share: float
    min_overlap_days: int


class DataQuality(_Strict):
    max_quarantined_share: float
    stale_quota_days: int
    implausible_daily_move: float


class PeerGroups(_Strict):
    field: str
    min_size: int


class ExpectedFunnel(_Strict):
    tolerance: float
    steps: dict[str, int]
    by_target_investor: dict[str, int]

    @model_validator(mode="after")
    def _steps_must_shrink(self) -> ExpectedFunnel:
        counts = list(self.steps.values())
        if counts != sorted(counts, reverse=True):
            raise ValueError("funnel steps must be non-increasing; check the filter order")
        return self


class UniverseConfig(_Strict):
    reference_date: dt.date
    lookback_months: int
    report_windows: list[int]
    filters: Filters
    fees: Fees
    data_quality: DataQuality
    peer_groups: PeerGroups
    expected_funnel: ExpectedFunnel


# ---------------------------------------------------------------------------
# profiles.yaml: what "best" means
# ---------------------------------------------------------------------------


class MetricSpec(_Strict):
    direction: Literal["high", "low"]
    label: str


class Eligibility(_Strict):
    target_investor: list[str]
    max_minimum_investment_brl: float | None
    max_redemption_days: int


class Profile(_Strict):
    label: str
    description: str
    eligibility: Eligibility
    weights: dict[str, int]
    jitter: dict[str, int]

    @model_validator(mode="after")
    def _weights_are_coherent(self) -> Profile:
        total = sum(self.weights.values())
        if total != 100:
            raise ValueError(f"weights must sum to 100, got {total}")
        unknown = set(self.jitter) - set(self.weights)
        if unknown:
            raise ValueError(f"jitter refers to weights that do not exist: {sorted(unknown)}")
        return self


class Winsorise(_Strict):
    lower: float
    upper: float


class Scoring(_Strict):
    winsorise: Winsorise
    min_dispersion: float


class Selection(_Strict):
    max_tracking_difference: float
    min_overlap_days: int


class Robustness(_Strict):
    simulations: int
    seed: int
    block_size_days: int
    top_n: int
    # How many funds the comparison list carries. It never touches the delivery:
    # the same walk down the same ranked order produces both, so the delivered
    # five are the first five of it.
    comparison_size: int
    report_split_by_variability: bool


class Backtest(_Strict):
    """Frozen before the backtest runs. Changing any of this after seeing a
    result would be fitting the method to the answer. See rule 11."""

    cut_dates: list[dt.date]
    random_portfolios: int
    seed: int
    success_percentile: int
    success_min_dates: int
    discontinued_fund_policy: Literal["carry_last_value", "exclude"]


class ProfilesConfig(_Strict):
    metrics: dict[str, MetricSpec]
    profiles: dict[str, Profile]
    scoring: Scoring
    selection: Selection
    robustness: Robustness
    backtest: Backtest

    @model_validator(mode="after")
    def _weights_refer_to_declared_metrics(self) -> ProfilesConfig:
        for name, profile in self.profiles.items():
            unknown = set(profile.weights) - set(self.metrics)
            if unknown:
                raise ValueError(f"profile {name!r} weights undeclared metrics: {sorted(unknown)}")
        return self


# ---------------------------------------------------------------------------
# sources.yaml: where the data comes from
# ---------------------------------------------------------------------------


class Source(_Strict):
    label: str
    url: str
    # Declared, not derived from the URL: the Central Bank's URL ends in a
    # query string, so the last path segment is the end date rather than a
    # file name.
    filename: str
    granularity: Literal["daily", "monthly", "yearly", "snapshot"]
    encoding: str = "latin-1"
    separator: str = ";"
    layouts: dict[str, dict[str, Any]] | None = None
    members: list[str] | None = None
    # The one member worth reading out of an archive that holds several. Takes
    # the same placeholders as `filename`.
    member: str | None = None
    note: str | None = None


class DownloadSettings(_Strict):
    timeout_seconds: int
    max_attempts: int
    backoff_seconds: float
    circuit_breaker_failures: int
    user_agent: str
    verify_content_type: bool


class CacheSettings(_Strict):
    directory: str
    reuse_if_hash_matches: bool
    manifest: str


class TransferSettings(_Strict):
    download: DownloadSettings
    cache: CacheSettings


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} should contain a mapping, got {type(loaded).__name__}")
    return loaded


def load_universe(path: Path) -> UniverseConfig:
    return UniverseConfig.model_validate(_read_yaml(path))


def load_profiles(path: Path) -> ProfilesConfig:
    return ProfilesConfig.model_validate(_read_yaml(path))


def load_sources(path: Path) -> dict[str, Source]:
    """The data sources themselves, keyed by short name."""
    raw = _read_yaml(path)
    return {name: Source.model_validate(body) for name, body in raw["sources"].items()}


def load_transfer_settings(path: Path) -> TransferSettings:
    """Retry, circuit breaker and cache behaviour, read from the same file."""
    raw = _read_yaml(path)
    return TransferSettings.model_validate({"download": raw["download"], "cache": raw["cache"]})
