from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PACKAGE_VERSION = "0.1.0"


@dataclass(frozen=True)
class SourceInfo:
    adapter: str
    query: str
    filters: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewInfo:
    status: str = "draft"
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChecksumEntry:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class RunManifest:
    manifest_version: str
    run_id: str
    created_at_utc: str
    package_version: str
    git_commit: str
    source: SourceInfo
    review: ReviewInfo
    outputs: list[ChecksumEntry]
    generated_sample_data: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_entries(paths: Iterable[str | Path], base_dir: str | Path | None = None) -> list[ChecksumEntry]:
    base = Path(base_dir).resolve() if base_dir is not None else None
    entries: list[ChecksumEntry] = []
    for path in sorted(Path(item) for item in paths):
        if not path.is_file():
            continue
        resolved = path.resolve()
        display = str(path)
        if base is not None:
            try:
                display = str(resolved.relative_to(base))
            except ValueError:
                display = str(path)
        entries.append(ChecksumEntry(path=display, sha256=sha256_file(resolved), size_bytes=resolved.stat().st_size))
    return entries


def discover_output_files(folder: str | Path) -> list[Path]:
    root = Path(folder)
    files: list[Path] = []
    for pattern in ("*.json", "*.md", "*.csv"):
        files.extend(path for path in root.rglob(pattern) if path.is_file())
    return sorted(set(files))


def build_manifest(
    *,
    source: SourceInfo,
    outputs: Iterable[str | Path],
    base_dir: str | Path | None = None,
    git_commit: str = "unknown",
    review: ReviewInfo | None = None,
    generated_sample_data: bool = False,
    created_at_utc: str | None = None,
) -> RunManifest:
    created = created_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = hashlib.sha256(f"{created}|{source.adapter}|{source.query}|{git_commit}".encode("utf-8")).hexdigest()[:16]
    return RunManifest(
        manifest_version="1.0",
        run_id=run_id,
        created_at_utc=created,
        package_version=PACKAGE_VERSION,
        git_commit=git_commit,
        source=source,
        review=review or ReviewInfo(),
        outputs=checksum_entries(outputs, base_dir=base_dir),
        generated_sample_data=generated_sample_data,
    )


def write_json(path: str | Path, payload: Any) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(output)


def write_manifest(path: str | Path, manifest: RunManifest) -> str:
    return write_json(path, manifest.to_dict())


def write_checksum_registry(path: str | Path, entries: list[ChecksumEntry]) -> str:
    payload = {entry.path: {"sha256": entry.sha256, "size_bytes": entry.size_bytes} for entry in entries}
    return write_json(path, payload)
