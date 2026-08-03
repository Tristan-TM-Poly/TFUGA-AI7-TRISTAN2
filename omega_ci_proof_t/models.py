from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

CLAIM_STATUSES = ("FERTILE", "PROTOTYPED", "MEASURED", "REFUTED", "BLOCKED")
TEST_STATUSES = ("PASSED", "FAILED", "SKIPPED", "ERROR")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(str(value) for value in values)))


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    subject_packages: tuple[str, ...]
    required_test_ids: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    domain_of_validity: tuple[str, ...] = ()
    status: str = "FERTILE"
    evidence_ttl_days: int = 30

    def __post_init__(self) -> None:
        if not self.claim_id.strip() or not self.statement.strip():
            raise ValueError("claim_id and statement are required")
        if self.status not in CLAIM_STATUSES:
            raise ValueError(f"unsupported claim status: {self.status}")
        if self.evidence_ttl_days < 1:
            raise ValueError("evidence_ttl_days must be positive")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("subject_packages", "required_test_ids", "assumptions", "domain_of_validity"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class TestSpec:
    test_id: str
    kind: str
    target: str
    command: str
    description: str
    source_claim_ids: tuple[str, ...]
    generated: bool = False
    source_rule_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source_claim_ids"] = list(self.source_claim_ids)
        return payload


@dataclass(frozen=True)
class ProofPlan:
    impact_plan_id: str
    changed_paths: tuple[str, ...]
    affected_packages: tuple[str, ...]
    claim_ids: tuple[str, ...]
    stale_claim_ids: tuple[str, ...]
    tests: tuple[TestSpec, ...]
    missing_test_ids: tuple[str, ...]
    environments: tuple[str, ...]
    completion_conditions: tuple[str, ...]
    limitations: tuple[str, ...]
    manifest_digest: str
    schema: str = "omega-ci-proof-plan/v1"

    @property
    def plan_id(self) -> str:
        return f"PROOFPLAN-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "impact_plan_id": self.impact_plan_id,
            "changed_paths": list(self.changed_paths),
            "affected_packages": list(self.affected_packages),
            "claim_ids": list(self.claim_ids),
            "stale_claim_ids": list(self.stale_claim_ids),
            "tests": [test.to_dict() for test in self.tests],
            "missing_test_ids": list(self.missing_test_ids),
            "environments": list(self.environments),
            "completion_conditions": list(self.completion_conditions),
            "limitations": list(self.limitations),
            "manifest_digest": self.manifest_digest,
        }

    @property
    def digest(self) -> str:
        return stable_digest(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "plan_id": self.plan_id,
            "digest": self.digest,
            **self.identity_payload(),
            "remote_mutations": 0,
            "automatic_merge": False,
        }


@dataclass(frozen=True)
class TestResult:
    test_id: str
    status: str
    environment: str
    command: str
    duration_ms: int
    output_digest: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.status not in TEST_STATUSES:
            raise ValueError(f"unsupported test status: {self.status}")
        if self.duration_ms < 0:
            raise ValueError("duration_ms cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactEvidence:
    path: str
    sha256: str
    size_bytes: int
    media_type: str = "application/octet-stream"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceDecision:
    status: str
    promotion_allowed: bool
    automatic_merge_allowed: bool = False
    human_review_required: bool = True
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


@dataclass(frozen=True)
class EvidenceBundle:
    run_id: str
    commit_sha: str
    proof_plan_id: str
    proof_plan_digest: str
    environment: Mapping[str, Any]
    subject: Mapping[str, Any]
    claims_tested: tuple[str, ...]
    test_results: tuple[TestResult, ...]
    properties: Mapping[str, bool]
    artifacts: tuple[ArtifactEvidence, ...]
    limitations: tuple[str, ...]
    decision: EvidenceDecision
    parent_bundle_ids: tuple[str, ...] = ()
    schema: str = "omega-ci-evidence/v1"

    def merkle_leaves(self) -> tuple[str, ...]:
        leaves = [self.proof_plan_digest, *self.claims_tested]
        leaves.extend(stable_digest(item.to_dict()) for item in self.test_results)
        leaves.extend(item.sha256 for item in self.artifacts)
        leaves.extend(stable_digest((key, value)) for key, value in sorted(self.properties.items()))
        leaves.extend(self.parent_bundle_ids)
        return tuple(leaves)

    @property
    def merkle_root(self) -> str:
        layer = list(self.merkle_leaves()) or [stable_digest(())]
        while len(layer) > 1:
            if len(layer) % 2:
                layer.append(layer[-1])
            layer = [stable_digest((layer[index], layer[index + 1])) for index in range(0, len(layer), 2)]
        return layer[0]

    @property
    def bundle_id(self) -> str:
        return f"EVIDENCE-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "commit_sha": self.commit_sha,
            "proof_plan_id": self.proof_plan_id,
            "proof_plan_digest": self.proof_plan_digest,
            "environment": dict(self.environment),
            "subject": dict(self.subject),
            "claims_tested": list(self.claims_tested),
            "test_results": [item.to_dict() for item in self.test_results],
            "properties": dict(self.properties),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "limitations": list(self.limitations),
            "decision": self.decision.to_dict(),
            "parent_bundle_ids": list(self.parent_bundle_ids),
            "merkle_root": self.merkle_root,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "bundle_id": self.bundle_id, **self.identity_payload()}


@dataclass(frozen=True)
class MMinusRule:
    rule_id: str
    failure_summary: str
    test_name: str
    import_line: str
    assertions: tuple[str, ...]
    source_failure_id: str
    risk: str = "normal"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["assertions"] = list(self.assertions)
        return payload


@dataclass(frozen=True)
class Finding:
    finding_id: str
    category: str
    severity: str
    message: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FailureDiagnostic:
    diagnostic_id: str
    failure_class: str
    stage: str
    failing_tests: tuple[str, ...]
    suspected_causes: tuple[str, ...]
    minimal_reproduction: Mapping[str, Any]
    proposed_actions: tuple[str, ...]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnostic_id": self.diagnostic_id,
            "failure_class": self.failure_class,
            "stage": self.stage,
            "failing_tests": list(self.failing_tests),
            "suspected_causes": list(self.suspected_causes),
            "minimal_reproduction": dict(self.minimal_reproduction),
            "proposed_actions": list(self.proposed_actions),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class AutonomyDecision:
    requested_level: str
    granted_level: str
    allowed: bool
    automatic_merge_allowed: bool
    human_review_required: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload
