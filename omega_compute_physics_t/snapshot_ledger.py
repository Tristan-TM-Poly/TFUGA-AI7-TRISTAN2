"""Commit-addressed repository snapshots for Omega Compute Physics R0.6.

Snapshots are provenance objects for static analysis and later benchmark evidence.
They can be created from a local read-only checkout or from externally supplied
Git tree records. A snapshot proves which bytes/blob identities were inventoried;
it does not prove that a checkout was isolated, trusted, or executable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


_DEFAULT_EXCLUDES = {".git", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"}


@dataclass(frozen=True)
class SnapshotFile:
    path: str
    size: int
    content_id: str
    extension: str


@dataclass(frozen=True)
class RepositorySnapshot:
    repository: str
    commit_sha: str
    files: tuple[SnapshotFile, ...]
    total_bytes: int
    extensions: Mapping[str, int]
    source: str
    status: str = "commit-addressed-static-snapshot"
    oak_warning: str = (
        "A snapshot records file/blob identity for reproducible static analysis. "
        "It does not establish runtime safety, dependency reproducibility or benchmark validity."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "files": [asdict(row) for row in self.files],
            "extensions": dict(sorted(self.extensions.items())),
        }


@dataclass(frozen=True)
class SnapshotDiff:
    repository: str
    old_commit: str
    new_commit: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]
    unchanged: int
    status: str = "static-snapshot-diff"
    oak_warning: str = (
        "Changed file identity is a trigger for re-analysis, not evidence of a "
        "performance regression or semantic change by itself."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extension(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return suffix if suffix else "<none>"


def snapshot_from_records(
    repository: str,
    commit_sha: str,
    records: Iterable[Mapping[str, Any]],
    *,
    source: str = "external-tree-records",
) -> RepositorySnapshot:
    """Build a snapshot from Git-tree-like records.

    Expected fields are ``path``, ``size`` and either ``content_id`` or ``sha``.
    Tree entries without a content id should be filtered by the caller.
    """
    rows: list[SnapshotFile] = []
    for record in records:
        path = str(record["path"])
        content_id = str(record.get("content_id") or record.get("sha") or "")
        if not content_id:
            raise ValueError(f"record {path!r} lacks content identity")
        size = int(record.get("size", 0))
        if size < 0:
            raise ValueError("file size cannot be negative")
        rows.append(SnapshotFile(path, size, content_id, _extension(path)))
    rows.sort(key=lambda row: row.path)
    extensions: dict[str, int] = {}
    for row in rows:
        extensions[row.extension] = extensions.get(row.extension, 0) + 1
    return RepositorySnapshot(
        repository=repository,
        commit_sha=commit_sha,
        files=tuple(rows),
        total_bytes=sum(row.size for row in rows),
        extensions=extensions,
        source=source,
    )


def snapshot_checkout(
    root: str | Path,
    *,
    repository: str,
    commit_sha: str,
    exclude_dirs: Sequence[str] = tuple(sorted(_DEFAULT_EXCLUDES)),
    max_file_bytes: int = 10_000_000,
) -> RepositorySnapshot:
    """Hash a local checkout without importing or executing repository code."""
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"snapshot root does not exist: {root_path}")
    excludes = set(exclude_dirs)
    records: list[dict[str, Any]] = []
    for path in sorted(p for p in root_path.rglob("*") if p.is_file()):
        if any(part in excludes for part in path.relative_to(root_path).parts):
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({
            "path": str(path.relative_to(root_path)),
            "size": size,
            "content_id": f"sha256:{digest}",
        })
    return snapshot_from_records(
        repository,
        commit_sha,
        records,
        source="local-checkout-sha256",
    )


def compare_snapshots(old: RepositorySnapshot, new: RepositorySnapshot) -> SnapshotDiff:
    if old.repository != new.repository:
        raise ValueError("snapshot diff requires the same repository")
    left = {row.path: row.content_id for row in old.files}
    right = {row.path: row.content_id for row in new.files}
    old_paths = set(left)
    new_paths = set(right)
    common = old_paths & new_paths
    return SnapshotDiff(
        repository=old.repository,
        old_commit=old.commit_sha,
        new_commit=new.commit_sha,
        added=tuple(sorted(new_paths - old_paths)),
        removed=tuple(sorted(old_paths - new_paths)),
        changed=tuple(sorted(path for path in common if left[path] != right[path])),
        unchanged=sum(left[path] == right[path] for path in common),
    )
