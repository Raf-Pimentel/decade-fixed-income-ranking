"""Downloading from the CVM without trusting it.

The portal has three failure modes worth defending against, and only the first
is the one people usually think of:

1. The connection fails. Retry, with growing waits.
2. The host stays down. Stop asking. Burning the retry budget of every
   remaining file to rediscover the same outage helps nobody, and hammering a
   struggling server is how you get blocked.
3. **The server answers HTTP 200 with an HTML error page.** This is the
   dangerous one: a pipeline that trusts the status code writes the error page
   to disk, reads zero rows out of it, and reports an empty universe without
   anything appearing to have failed.
"""

from __future__ import annotations

import datetime as dt
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from tenacity import RetryCallState, Retrying, stop_after_attempt, wait_exponential

from ranking.config import DownloadSettings
from ranking.extract import manifest
from ranking.extract.manifest import ManifestEntry


class DownloadError(RuntimeError):
    """The file could not be fetched after exhausting the retries."""


class CircuitOpenError(DownloadError):
    """This host has failed too many times in a row; we stopped asking."""


class InvalidPayloadError(DownloadError):
    """The response arrived, but it is not the file it claims to be."""


@dataclass(frozen=True)
class DownloadResult:
    entry: ManifestEntry
    reused: bool


_ZIP_MAGIC = b"PK\x03\x04"
_HTML_START = re.compile(rb"^\s*(<!doctype|<html|<\?xml)", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\{(yyyymm|yyyy|start|end)\}")


def resolve_url(
    template: str,
    year: int | None = None,
    month: int | None = None,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> str:
    """Fill `{yyyy}`, `{yyyymm}`, `{start}` and `{end}` in a source URL.

    Dates are rendered day-first, which is what the Central Bank's series API
    expects. Sending them month-first would fetch a different window and
    succeed, which is worse than failing.

    Refuses to leave a placeholder behind. Producing a URL containing the
    literal text `{yyyymm}` would turn a configuration mistake into a 404 that
    looks like the CVM being unavailable.
    """
    values: dict[str, str] = {}
    if year is not None:
        values["yyyy"] = f"{year:04d}"
        if month is not None:
            values["yyyymm"] = f"{year:04d}{month:02d}"
    if start is not None:
        values["start"] = start.strftime("%d/%m/%Y")
    if end is not None:
        values["end"] = end.strftime("%d/%m/%Y")

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(f"URL template needs {{{name}}} but no value was given: {template}")
        return values[name]

    return _PLACEHOLDER.sub(replace, template)


def verify_payload(content: bytes, url: str) -> None:
    """Check that the bytes are plausibly the file we asked for."""
    if not content:
        raise InvalidPayloadError(f"{url} returned an empty body")

    if _HTML_START.match(content[:200]):
        raise InvalidPayloadError(
            f"{url} returned an HTML page, not data. The CVM serves its error "
            "pages with HTTP 200, so the status code alone means nothing here."
        )

    path = urlsplit(url).path.lower()
    if path.endswith(".zip") and not content.startswith(_ZIP_MAGIC):
        raise InvalidPayloadError(f"{url} does not start with the ZIP signature")


class Downloader:
    """Fetches files, retries, and refuses to keep asking a dead host.

    The breaker counts *consecutive* failures per host and, once open, stays
    open for the life of this downloader. For a batch job that is the right
    behaviour: if the CVM is down, the run should end quickly with a clear
    message rather than limp along for an hour and produce a partial universe.
    """

    def __init__(
        self,
        policy: DownloadSettings,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._policy = policy
        self._client = client or httpx.Client(follow_redirects=True)
        self._sleep = sleep
        self._consecutive_failures: dict[str, int] = {}

    def fetch(
        self,
        url: str,
        destination: Path,
        known: ManifestEntry | None = None,
    ) -> DownloadResult:
        """Download `url` to `destination`, reusing it if it is already there."""
        if known is not None and known.matches(destination):
            return DownloadResult(entry=known, reused=True)

        host = urlsplit(url).hostname or url
        self._check_breaker(host)

        content = self._get_with_retries(url, host)

        try:
            verify_payload(content, url)
        except InvalidPayloadError:
            # A bad payload is the host misbehaving, so it counts towards the
            # breaker just like a connection error does.
            self._record_failure(host)
            raise

        self._consecutive_failures[host] = 0
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Write via a temporary name so an interrupted run never leaves a
        # half-written file that looks like data.
        staging = destination.with_suffix(destination.suffix + ".part")
        staging.write_bytes(content)
        staging.replace(destination)
        return DownloadResult(entry=manifest.record(destination), reused=False)

    # -- internals ---------------------------------------------------------

    def _check_breaker(self, host: str) -> None:
        failures = self._consecutive_failures.get(host, 0)
        if failures >= self._policy.circuit_breaker_failures:
            raise CircuitOpenError(
                f"{host} failed {failures} requests in a row; not sending further requests. "
                "Check whether the portal is up before rerunning."
            )

    def _record_failure(self, host: str) -> None:
        """Counted per failed *request*, not per failed file.

        The server experiences requests, so that is the unit that matters for
        deciding it has had enough. Counting whole files instead would let a
        three-attempt retry policy fire fifteen requests at a dead host before
        the breaker noticed.
        """
        self._consecutive_failures[host] = self._consecutive_failures.get(host, 0) + 1

    def _get_with_retries(self, url: str, host: str) -> bytes:
        def before_sleep(state: RetryCallState) -> None:
            if state.next_action is not None:
                self._sleep(state.next_action.sleep)

        retrying = Retrying(
            stop=stop_after_attempt(self._policy.max_attempts),
            wait=wait_exponential(multiplier=self._policy.backoff_seconds),
            before_sleep=before_sleep,
            sleep=lambda _seconds: None,  # the waiting is done by before_sleep
            reraise=True,
        )
        try:
            for attempt in retrying:
                with attempt:
                    try:
                        response = self._client.get(
                            url,
                            timeout=self._policy.timeout_seconds,
                            headers={"User-Agent": self._policy.user_agent},
                        )
                        response.raise_for_status()
                    except httpx.HTTPError:
                        self._record_failure(host)
                        raise
                    return response.content
        except httpx.HTTPError as error:
            raise DownloadError(f"could not download {url}: {error}") from error
        raise DownloadError(f"could not download {url}")  # pragma: no cover - unreachable
