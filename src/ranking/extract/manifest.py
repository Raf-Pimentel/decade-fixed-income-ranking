"""A record of exactly which bytes produced a given ranking.

The CVM restates data by overwriting the published file in place. There is no
version, no changelog, and no way to ask for yesterday's copy. So a ranking
dated December 2025 cannot be reproduced three months later unless we wrote
down what we actually read at the time, which is what this does.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

_CHUNK = 1 << 20  # hash in 1 MiB chunks so a 200 MB zip never lands in memory


@dataclass(frozen=True)
class ManifestEntry:
    name: str
    sha256: str
    size_bytes: int
    downloaded_at: dt.datetime

    def matches(self, path: Path) -> bool:
        """Whether the file on disk is still the one described here."""
        if not path.exists() or path.stat().st_size != self.size_bytes:
            return False
        return sha256(path) == self.sha256


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def record(path: Path, downloaded_at: dt.datetime | None = None) -> ManifestEntry:
    return ManifestEntry(
        name=path.name,
        sha256=sha256(path),
        size_bytes=path.stat().st_size,
        downloaded_at=downloaded_at or dt.datetime.now(dt.UTC),
    )


def write(entries: dict[str, ManifestEntry], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        name: {**asdict(entry), "downloaded_at": entry.downloaded_at.isoformat()}
        for name, entry in sorted(entries.items())
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load(path: Path) -> dict[str, ManifestEntry]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        name: ManifestEntry(
            name=body["name"],
            sha256=body["sha256"],
            size_bytes=body["size_bytes"],
            downloaded_at=dt.datetime.fromisoformat(body["downloaded_at"]),
        )
        for name, body in raw.items()
    }
