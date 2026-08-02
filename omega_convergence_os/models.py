from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping


class ConflictKind(str, Enum):
    FILE = "file"
    API = "api"
    DEPENDENCY = "dependency"
    SCHEMA = "schema"
    EPISTEMIC = "epistemic"
    POLICY = "policy"
    RESOURCE = "resource"
    BINARY = "binary"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FileChange:
    path: str
    status: str
    sha256: str | None = None
    size_bytes: int | None = None
    binary: bool = False

    def __post_init__(self) -> None:
        if self.status not in {"added", "modified", "deleted", "renamed", "unchanged"}:
            raise ValueError(f"unsupported file status: {self.status}")
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ValueError(f"unsafe repository path: {self.path!r}")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")


@dataclass(frozen=True)
class Conflict:
    kind: ConflictKind
    severity: Severity
    key: str
    message: str
    base_value: Any = None
    head_value: Any = None
    recommended_action: str = "review"
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class BranchDNA:
    branch: str
    base_sha: str
    head_sha: str
    files: tuple[FileChange, ...] = ()
    public_symbols: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    scripts: Mapping[str, str] = field(default_factory=dict)
    workflow_permissions: Mapping[str, str] = field(default_factory=dict)
    epistemic_statuses: Mapping[str, str] = field(default_factory=dict)
    claims: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.branch:
            raise ValueError("branch is required")
        for name, value in (("base_sha", self.base_sha), ("head_sha", self.head_sha)):
            if not value or len(value) < 7:
                raise ValueError(f"{name} must contain a commit identifier")

    def canonical_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["files"] = sorted(payload["files"], key=lambda item: item["path"])
        payload["public_symbols"] = {
            key: list(value) for key, value in sorted(self.public_symbols.items())
        }
        payload["scripts"] = dict(sorted(self.scripts.items()))
        payload["workflow_permissions"] = dict(sorted(self.workflow_permissions.items()))
        payload["epistemic_statuses"] = dict(sorted(self.epistemic_statuses.items()))
        payload["claims"] = sorted(self.claims)
        payload["tests"] = sorted(self.tests)
        payload["risks"] = sorted(self.risks)
        return payload

    def digest(self) -> str:
        encoded = json.dumps(
            self.canonical_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class MergePlan:
    base_sha: str
    head_sha: str
    strategy_by_path: Mapping[str, str]
    conflicts: tuple[Conflict, ...]
    required_tests: tuple[str, ...]
    preservation_paths: tuple[str, ...]
    rollback_steps: tuple[str, ...]
    verdict: str
    automatic_merge_allowed: bool = False

    def __post_init__(self) -> None:
        if self.automatic_merge_allowed:
            raise ValueError("R0.1 never authorizes automatic merge")


@dataclass(frozen=True)
class MergeReceipt:
    receipt_id: str
    base_sha: str
    head_sha: str
    result_sha: str | None
    branch_dna_sha256: str
    conflict_count: int
    high_or_critical_conflicts: int
    tests: tuple[str, ...]
    artifacts: tuple[str, ...]
    known_residues: tuple[str, ...]
    oak_verdict: str
    automatic_scientific_promotion: bool = False
    automatic_merge: bool = False

    def __post_init__(self) -> None:
        if self.automatic_scientific_promotion or self.automatic_merge:
            raise ValueError("automatic promotion and merge are forbidden in R0.1")
        if self.conflict_count < 0 or self.high_or_critical_conflicts < 0:
            raise ValueError("conflict counts must be non-negative")

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        encoded = json.dumps(
            self.canonical_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def stable_sha256(parts: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
