"""Downloading from the CVM without trusting it.

Three separate things are being tested, because three separate things go
wrong in practice:

- the connection fails and should be retried, with growing waits;
- the server keeps failing and we should stop asking rather than hammer it;
- the server answers HTTP 200 with an HTML error page, which is the CVM's
  actual behaviour and the one that silently poisons a pipeline.

Every request here is served by an in-memory transport. Nothing reaches the
network, and the tests assert on how many times the handler was called.
"""

from __future__ import annotations

import httpx
import pytest

from ranking.config import DownloadSettings
from ranking.extract import http

ZIP_BYTES = b"PK\x03\x04" + b"\x00" * 40
HTML_ERROR = b"<!DOCTYPE html><html><body>Servico temporariamente indisponivel</body></html>"


@pytest.fixture
def policy() -> DownloadSettings:
    return DownloadSettings(
        timeout_seconds=5,
        max_attempts=3,
        backoff_seconds=2,
        circuit_breaker_failures=5,
        user_agent="test-agent/1.0",
        verify_content_type=True,
    )


@pytest.fixture
def waits() -> list[float]:
    """Collects what the downloader would have slept, so the tests can assert
    on the backoff without actually waiting."""
    return []


def make_downloader(policy, handler, waits) -> http.Downloader:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return http.Downloader(policy, client=client, sleep=waits.append)


# --------------------------------------------------------------------------
# The happy path
# --------------------------------------------------------------------------


def test_a_successful_download_writes_the_file(policy, waits, tmp_path) -> None:
    downloader = make_downloader(
        policy, lambda request: httpx.Response(200, content=ZIP_BYTES), waits
    )
    target = tmp_path / "inf_diario_fi_202512.zip"

    result = downloader.fetch("https://dados.cvm.gov.br/x.zip", target)

    assert target.read_bytes() == ZIP_BYTES
    assert result.entry.size_bytes == len(ZIP_BYTES)
    assert len(result.entry.sha256) == 64
    assert result.reused is False
    assert waits == []


def test_the_configured_user_agent_is_sent(policy, waits, tmp_path) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("user-agent", ""))
        return httpx.Response(200, content=ZIP_BYTES)

    make_downloader(policy, handler, waits).fetch("https://x/y.zip", tmp_path / "y.zip")
    assert seen == ["test-agent/1.0"]


# --------------------------------------------------------------------------
# Retry
# --------------------------------------------------------------------------


def test_a_transient_failure_is_retried(policy, waits, tmp_path) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(503)
        return httpx.Response(200, content=ZIP_BYTES)

    result = make_downloader(policy, handler, waits).fetch("https://x/y.zip", tmp_path / "y.zip")

    assert len(calls) == 3
    assert result.entry.size_bytes == len(ZIP_BYTES)


def test_waits_grow_between_attempts(policy, waits, tmp_path) -> None:
    """Hammering a struggling server every 100ms is how you get blocked."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    with pytest.raises(http.DownloadError):
        make_downloader(policy, handler, waits).fetch("https://x/y.zip", tmp_path / "y.zip")

    assert len(waits) == policy.max_attempts - 1
    assert waits == sorted(waits)
    assert waits[0] < waits[-1]


def test_it_gives_up_after_the_configured_attempts(policy, waits, tmp_path) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(500)

    with pytest.raises(http.DownloadError):
        make_downloader(policy, handler, waits).fetch("https://x/y.zip", tmp_path / "y.zip")

    assert len(calls) == policy.max_attempts


def test_a_failed_download_leaves_no_partial_file(policy, waits, tmp_path) -> None:
    """A half-written file that looks like data is worse than no file."""
    target = tmp_path / "y.zip"
    with pytest.raises(http.DownloadError):
        make_downloader(policy, lambda r: httpx.Response(500), waits).fetch(
            "https://x/y.zip", target
        )
    assert not target.exists()


# --------------------------------------------------------------------------
# Circuit breaker
# --------------------------------------------------------------------------


def test_the_breaker_opens_after_repeated_failures(policy, waits, tmp_path) -> None:
    """Once the host has clearly gone away, stop asking and say so plainly,
    instead of burning the retry budget of every remaining file."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(500)

    downloader = make_downloader(policy, handler, waits)
    for index in range(2):
        with pytest.raises(http.DownloadError):
            downloader.fetch(f"https://dados.cvm.gov.br/{index}.zip", tmp_path / f"{index}.zip")

    before = len(calls)
    with pytest.raises(http.CircuitOpenError):
        downloader.fetch("https://dados.cvm.gov.br/third.zip", tmp_path / "third.zip")

    assert len(calls) == before, "an open breaker must not send another request"


def test_the_breaker_is_per_host(policy, waits, tmp_path) -> None:
    """The Central Bank being down says nothing about the CVM."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "broken.example":
            return httpx.Response(500)
        return httpx.Response(200, content=ZIP_BYTES)

    downloader = make_downloader(policy, handler, waits)
    for index in range(2):
        with pytest.raises(http.DownloadError):
            downloader.fetch(f"https://broken.example/{index}.zip", tmp_path / f"{index}.zip")

    result = downloader.fetch("https://dados.cvm.gov.br/ok.zip", tmp_path / "ok.zip")
    assert result.entry.size_bytes == len(ZIP_BYTES)


def test_a_success_resets_the_failure_count(policy, waits, tmp_path) -> None:
    state = {"fail": True}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500) if state["fail"] else httpx.Response(200, content=ZIP_BYTES)

    downloader = make_downloader(policy, handler, waits)
    with pytest.raises(http.DownloadError):
        downloader.fetch("https://host/a.zip", tmp_path / "a.zip")

    state["fail"] = False
    downloader.fetch("https://host/b.zip", tmp_path / "b.zip")

    state["fail"] = True
    # the counter restarted, so one failure is not enough to open the breaker
    with pytest.raises(http.DownloadError):
        downloader.fetch("https://host/c.zip", tmp_path / "c.zip")


# --------------------------------------------------------------------------
# The CVM answers errors with HTTP 200
# --------------------------------------------------------------------------


def test_an_html_error_page_is_rejected(policy, waits, tmp_path) -> None:
    """This is the failure that matters. The status code says 200, the body is
    an error page, and a pipeline that trusts the status writes it to disk and
    reports zero funds without anything looking wrong."""
    downloader = make_downloader(policy, lambda r: httpx.Response(200, content=HTML_ERROR), waits)

    with pytest.raises(http.InvalidPayloadError):
        downloader.fetch("https://dados.cvm.gov.br/x.zip", tmp_path / "x.zip")


def test_a_zip_that_is_not_a_zip_is_rejected(policy, waits, tmp_path) -> None:
    downloader = make_downloader(policy, lambda r: httpx.Response(200, content=b"nope"), waits)
    with pytest.raises(http.InvalidPayloadError):
        downloader.fetch("https://x/y.zip", tmp_path / "y.zip")


def test_an_empty_body_is_rejected(policy, waits, tmp_path) -> None:
    downloader = make_downloader(policy, lambda r: httpx.Response(200, content=b""), waits)
    with pytest.raises(http.InvalidPayloadError):
        downloader.fetch("https://x/y.csv", tmp_path / "y.csv")


def test_a_csv_is_accepted(policy, waits, tmp_path) -> None:
    csv = "CNPJ_FUNDO_CLASSE;DT_COMPTC\n00017024000153;2025-12-01\n".encode("latin-1")
    downloader = make_downloader(policy, lambda r: httpx.Response(200, content=csv), waits)
    result = downloader.fetch("https://x/y.csv", tmp_path / "y.csv")
    assert result.entry.size_bytes == len(csv)


def test_rejected_payloads_leave_no_file(policy, waits, tmp_path) -> None:
    target = tmp_path / "x.zip"
    downloader = make_downloader(policy, lambda r: httpx.Response(200, content=HTML_ERROR), waits)
    with pytest.raises(http.InvalidPayloadError):
        downloader.fetch("https://x/x.zip", target)
    assert not target.exists()


# --------------------------------------------------------------------------
# Cache — the same reference date must not re-download 200 MB
# --------------------------------------------------------------------------


def test_an_unchanged_file_is_not_downloaded_again(policy, waits, tmp_path) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, content=ZIP_BYTES)

    downloader = make_downloader(policy, handler, waits)
    target = tmp_path / "y.zip"

    first = downloader.fetch("https://x/y.zip", target)
    second = downloader.fetch("https://x/y.zip", target, known=first.entry)

    assert len(calls) == 1
    assert second.reused is True
    assert second.entry.sha256 == first.entry.sha256


def test_a_tampered_cache_is_downloaded_again(policy, waits, tmp_path) -> None:
    """If the bytes on disk no longer match what the manifest recorded, the
    cache is not a cache — it is an unknown file."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, content=ZIP_BYTES)

    downloader = make_downloader(policy, handler, waits)
    target = tmp_path / "y.zip"
    first = downloader.fetch("https://x/y.zip", target)

    target.write_bytes(b"something else entirely")
    second = downloader.fetch("https://x/y.zip", target, known=first.entry)

    assert len(calls) == 2
    assert second.reused is False


# --------------------------------------------------------------------------
# Building URLs from the source templates
# --------------------------------------------------------------------------


def test_monthly_urls_are_filled_in() -> None:
    template = "https://dados.cvm.gov.br/.../inf_diario_fi_{yyyymm}.zip"
    assert http.resolve_url(template, year=2025, month=12).endswith("inf_diario_fi_202512.zip")


def test_single_digit_months_are_padded() -> None:
    template = "https://x/{yyyymm}.zip"
    assert http.resolve_url(template, year=2025, month=3) == "https://x/202503.zip"


def test_yearly_urls_are_filled_in() -> None:
    assert http.resolve_url("https://x/extrato_fi_{yyyy}.csv", year=2025) == (
        "https://x/extrato_fi_2025.csv"
    )


def test_a_template_with_no_placeholder_is_left_alone() -> None:
    url = "https://www.anbima.com.br/informacoes/ima/arqs/ima_completo.xls"
    assert http.resolve_url(url) == url


def test_a_missing_placeholder_value_is_an_error() -> None:
    """Better than quietly producing a URL with the literal text {yyyymm}."""
    with pytest.raises(ValueError):
        http.resolve_url("https://x/{yyyymm}.zip", year=2025)


# --------------------------------------------------------------------------
# Date-bounded sources
#
# The Central Bank's series API answers 406 Not Acceptable when the requested
# range is too wide — eleven years is refused, fourteen months is fine. Asking
# for the whole series, which is what an unbounded URL does, always fails. So
# the CDI URL has to carry the window we actually need.
# --------------------------------------------------------------------------


def test_start_and_end_dates_are_filled_in() -> None:
    import datetime as dt

    template = "https://api.bcb.gov.br/...?dataInicial={start}&dataFinal={end}"
    resolved = http.resolve_url(template, start=dt.date(2025, 1, 2), end=dt.date(2025, 12, 31))
    assert resolved.endswith("dataInicial=02/01/2025&dataFinal=31/12/2025")


def test_dates_use_the_brazilian_day_first_format() -> None:
    """`03/04/2025` means 3 April here. Sending it month-first would silently
    fetch the wrong window rather than fail."""
    import datetime as dt

    assert http.resolve_url("{start}", start=dt.date(2025, 4, 3)) == "03/04/2025"


def test_a_missing_date_value_is_an_error() -> None:
    with pytest.raises(ValueError):
        http.resolve_url("https://x?dataInicial={start}")


# --------------------------------------------------------------------------
# Cache file names
#
# Deriving the file name from the URL works for the CVM, whose URLs end in the
# file, and breaks for the Central Bank, whose URL ends in a query string —
# the CDI series was landing on disk as a file called "2025".
# --------------------------------------------------------------------------


def test_each_source_declares_its_cache_file_name(config_dir) -> None:
    from ranking.config import load_sources

    for name, source in load_sources(config_dir / "sources.yaml").items():
        assert source.filename, f"source {name!r} must declare a filename"


def test_the_cdi_file_name_is_not_taken_from_the_query_string(config_dir) -> None:
    from ranking.config import load_sources

    cdi = load_sources(config_dir / "sources.yaml")["cdi"]
    assert http.resolve_url(cdi.filename, year=2025) == "cdi_2025.json"
