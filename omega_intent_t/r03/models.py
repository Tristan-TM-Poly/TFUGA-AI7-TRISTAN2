from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FileRecord:
    path: str
    size_bytes: int
    sha256: str
    kind: str
    package: str
    imports: tuple[str, ...] = ()
    generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["imports"] = list(self.imports)
        return payload


@dataclass(frozen=True)
class WorkflowRule:
    name: str
    path: str
    path_patterns: tuple[str, ...]
    has_concurrency_cancellation: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "path_patterns": list(self.path_patterns),
            "has_concurrency_cancellation": self.has_concurrency_cancellation,
        }


@dataclass(frozen=True)
class RepoTwinManifest:
    root: str
    files: tuple[FileRecord, ...]
    workflows: tuple[WorkflowRule, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    test_edges: tuple[tuple[str, str], ...]
    ignored_directories: tuple[str, ...]
    schema: str = "omega-intent-repotwin/v3"

    @property
    def root_digest(self) -> str:
        return stable_digest({
            "files": [item.to_dict() for item in self.files],
            "workflows": [item.to_dict() for item in self.workflows],
            "dependency_edges": [list(edge) for edge in self.dependency_edges],
            "test_edges": [list(edge) for edge in self.test_edges],
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "root": self.root,
            "root_digest": self.root_digest,
            "files": [item.to_dict() for item in self.files],
            "workflows": [item.to_dict() for item in self.workflows],
            "dependency_edges": [list(edge) for edge in self.dependency_edges],
            "test_edges": [list(edge) for edge in self.test_edges],
            "ignored_directories": list(self.ignored_directories),
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class CostEstimate:
    focused_test_units: int
    integration_test_units: int
    workflow_units: int
    file_scan_units: int
    relative_cost_score: float
    interpretation: str = "relative planning heuristic, not billed cost or runtime guarantee"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ImpactPlan:
    changed_paths: tuple[str, ...]
    affected_packages: tuple[str, ...]
    affected_tests: tuple[str, ...]
    selected_workflows: tuple[str, ...]
    tiers: tuple[str, ...]
    reasons: tuple[str, ...]
    full_suite_required: bool
    unknown_paths: tuple[str, ...]
    cost: CostEstimate
    manifest_digest: str
    schema: str = "omega-intent-impact-plan/v3"

    @property
    def plan_id(self) -> str:
        return f"IMPACT-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "changed_paths": list(self.changed_paths),
            "affected_packages": list(self.affected_packages),
            "affected_tests": list(self.affected_tests),
            "selected_workflows": list(self.selected_workflows),
            "tiers": list(self.tiers),
            "reasons": list(self.reasons),
            "full_suite_required": self.full_suite_required,
            "unknown_paths": list(self.unknown_paths),
            "cost": self.cost.to_dict(),
            "manifest_digest": self.manifest_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "plan_id": self.plan_id,
            **self.identity_payload(),
            "automatic_merge": False,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class ValidationReceipt:
    validator: str
    status: str
    command: str = ""
    evidence_digest: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProofArtifact:
    artifact_id: str
    path: str
    sha256: str
    size_bytes: int
    media_type: str
    provenance: tuple[str, ...]
    derived_from: tuple[str, ...]
    validations: tuple[ValidationReceipt, ...]
    epistemic_status: str
    uncertainty: Mapping[str, Any] = field(default_factory=dict)
    risks: tuple[str, ...] = ()
    publication_authorized: bool = False
    schema: str = "omega-proof-artifact/v3"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "artifact_id": self.artifact_id,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "media_type": self.media_type,
            "provenance": list(self.provenance),
            "derived_from": list(self.derived_from),
            "validations": [item.to_dict() for item in self.validations],
            "epistemic_status": self.epistemic_status,
            "uncertainty": dict(self.uncertainty),
            "risks": list(self.risks),
            "publication_authorized": self.publication_authorized,
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
        }


@dataclass(frozen=True)
class OakResult:
    passed: bool
    checks: tuple[Mapping[str, Any], ...]
    warnings: tuple[str, ...] = ()
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False
    remote_mutations: int = 0
    automatic_merge: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega-intent-r03-oak/v3",
            "passed": self.passed,
            "checks": [dict(item) for item in self.checks],
            "warnings": list(self.warnings),
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
            "remote_mutations": self.remote_mutations,
            "automatic_merge": self.automatic_merge,
        }


def sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))
