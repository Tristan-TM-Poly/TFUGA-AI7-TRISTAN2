from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import PullRequestSnapshot, RepositorySnapshot, canonical_json, sha256_digest


@dataclass(frozen=True, slots=True)
class SnapshotBundle:
    repositories: tuple[RepositorySnapshot, ...]
    pull_requests: tuple[PullRequestSnapshot, ...]
    source: str = "offline_snapshot"
    completeness: str = "declared_by_producer"
    generated_at: str | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        repo_names = [repo.full_name for repo in self.repositories]
        if len(repo_names) != len(set(repo_names)):
            raise ValueError("duplicate repositories in snapshot")
        repo_set = set(repo_names)
        pr_ids = [pr.pr_id for pr in self.pull_requests]
        if len(pr_ids) != len(set(pr_ids)):
            raise ValueError("duplicate pull requests in snapshot")
        unknown = sorted({pr.repo_full_name for pr in self.pull_requests} - repo_set)
        if unknown:
            raise ValueError(f"pull requests reference unknown repositories: {unknown}")

    @property
    def digest(self) -> str:
        return sha256_digest(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "completeness": self.completeness,
            "generated_at": self.generated_at,
            "repositories": [repo.to_dict() for repo in self.repositories],
            "pull_requests": [pr.to_dict() for pr in self.pull_requests],
            "metadata": dict(self.metadata or {}),
        }
        if include_digest:
            payload["digest"] = sha256_digest(payload)
        return payload

    def summary(self) -> dict[str, Any]:
        public = sum(repo.visibility == "public" for repo in self.repositories)
        private = sum(repo.visibility == "private" for repo in self.repositories)
        drafts = sum(pr.draft for pr in self.pull_requests)
        mergeable = sum(pr.mergeable is True for pr in self.pull_requests)
        return {
            "repository_count": len(self.repositories),
            "public_repository_count": public,
            "private_repository_count": private,
            "open_pull_request_count": sum(pr.state == "open" for pr in self.pull_requests),
            "draft_pull_request_count": drafts,
            "known_mergeable_pull_request_count": mergeable,
            "snapshot_digest": self.digest,
            "completeness": self.completeness,
        }

    def write(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SnapshotBundle":
        expected = value.get("digest")
        payload = {key: val for key, val in value.items() if key != "digest"}
        if expected is not None and sha256_digest(payload) != expected:
            raise ValueError("snapshot digest mismatch")
        return cls(
            repositories=tuple(RepositorySnapshot.from_dict(item) for item in value.get("repositories", ())),
            pull_requests=tuple(PullRequestSnapshot.from_dict(item) for item in value.get("pull_requests", ())),
            source=str(value.get("source", "offline_snapshot")),
            completeness=str(value.get("completeness", "declared_by_producer")),
            generated_at=value.get("generated_at"),
            metadata=dict(value.get("metadata", {})),
        )

    @classmethod
    def read(cls, path: str | Path) -> "SnapshotBundle":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def bundle_from_rows(
    repositories: Iterable[Mapping[str, Any]],
    pull_requests: Iterable[Mapping[str, Any]],
    *,
    source: str,
    completeness: str,
    generated_at: str | None = None,
) -> SnapshotBundle:
    return SnapshotBundle(
        repositories=tuple(RepositorySnapshot.from_dict(item) for item in repositories),
        pull_requests=tuple(PullRequestSnapshot.from_dict(item) for item in pull_requests),
        source=source,
        completeness=completeness,
        generated_at=generated_at,
    )
