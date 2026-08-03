from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

EVIDENCE_STATES = ("CURRENT", "STALE", "EXPIRED", "SUPERSEDED", "INVALIDATED", "REVOKED")
EPISTEMIC_STATES = (
    "UNKNOWN", "FERTILE", "HYPOTHESIZED", "PLANNED", "GENERATED", "COMPILED",
    "TESTED", "PROTOTYPED", "SIMULATED", "MEASURED", "REPRODUCED",
    "FORMALLY_CHECKED", "REFUTED", "BLOCKED", "EXPIRED",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(str(value) for value in values)))


@dataclass(frozen=True)
class EvidenceValidity:
    bundle_id: str
    claim_ids: tuple[str, ...]
    observed_at: str
    evaluated_at: str
    expires_at: str
    status: str
    reasons: tuple[str, ...]
    invalidated_by: tuple[str, ...]
    refresh_requirements: tuple[str, ...]
    source_digest: str
    schema: str = "omega-ci-evidence-validity/v2"

    def __post_init__(self) -> None:
        if self.status not in EVIDENCE_STATES:
            raise ValueError(f"unsupported evidence status: {self.status}")

    @property
    def validity_id(self) -> str:
        return f"VALIDITY-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "claim_ids": list(self.claim_ids),
            "observed_at": self.observed_at,
            "evaluated_at": self.evaluated_at,
            "expires_at": self.expires_at,
            "status": self.status,
            "reasons": list(self.reasons),
            "invalidated_by": list(self.invalidated_by),
            "refresh_requirements": list(self.refresh_requirements),
            "source_digest": self.source_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "validity_id": self.validity_id, **self.identity_payload()}


@dataclass(frozen=True)
class ClaimCoverage:
    claim_id: str
    required_kinds: tuple[str, ...]
    observed_kinds: tuple[str, ...]
    missing_kinds: tuple[str, ...]
    dimensions: Mapping[str, bool]
    score: float
    weight: float
    blocked: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "required_kinds": list(self.required_kinds),
            "observed_kinds": list(self.observed_kinds),
            "missing_kinds": list(self.missing_kinds),
            "dimensions": dict(self.dimensions),
            "score": self.score,
            "weight": self.weight,
            "blocked": self.blocked,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class ClaimCoverageReport:
    claims: tuple[ClaimCoverage, ...]
    weighted_score: float
    covered_claims: int
    blocked_claims: int
    uncovered_claims: int
    schema: str = "omega-ci-claim-coverage/v2"

    @property
    def report_id(self) -> str:
        return f"COVERAGE-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "claims": [claim.to_dict() for claim in self.claims],
            "weighted_score": self.weighted_score,
            "covered_claims": self.covered_claims,
            "blocked_claims": self.blocked_claims,
            "uncovered_claims": self.uncovered_claims,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "report_id": self.report_id, **self.identity_payload()}


@dataclass(frozen=True)
class PromotionProof:
    claim_id: str
    from_status: str
    to_status: str
    evidence_bundle_ids: tuple[str, ...]
    validity_statuses: tuple[str, ...]
    coverage_score: float
    coverage_threshold: float
    prerequisites: Mapping[str, bool]
    decision: str
    reasons: tuple[str, ...]
    human_review_required: bool = True
    automatic_merge_allowed: bool = False
    schema: str = "omega-ci-promotion-proof/v2"

    @property
    def proof_id(self) -> str:
        return f"PROMOTION-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "evidence_bundle_ids": list(self.evidence_bundle_ids),
            "validity_statuses": list(self.validity_statuses),
            "coverage_score": self.coverage_score,
            "coverage_threshold": self.coverage_threshold,
            "prerequisites": dict(self.prerequisites),
            "decision": self.decision,
            "reasons": list(self.reasons),
            "human_review_required": self.human_review_required,
            "automatic_merge_allowed": self.automatic_merge_allowed,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "proof_id": self.proof_id, **self.identity_payload()}


@dataclass(frozen=True)
class CapabilityToken:
    agent: str
    run_id: str
    level: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    scope: tuple[str, ...]
    issued_at: str
    expires_at: str
    revocable: bool = True
    schema: str = "omega-ci-capability-token/v2"

    @property
    def token_id(self) -> str:
        return f"CAP-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "run_id": self.run_id,
            "level": self.level,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "scope": list(self.scope),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revocable": self.revocable,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "token_id": self.token_id, **self.identity_payload()}


@dataclass(frozen=True)
class ConstitutionAudit:
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    immutable_principles: tuple[str, ...]
    maximum_authorized_level: str
    constitution_digest: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("errors", "warnings", "immutable_principles"):
            payload[key] = list(payload[key])
        payload["schema"] = "omega-ci-constitution-audit/v2"
        payload["automatic_merge_allowed"] = False
        return payload


@dataclass(frozen=True)
class SupplyChainFinding:
    workflow_path: str
    action: str
    reference: str
    severity: str
    message: str
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticProofKey:
    claim_digest: str
    code_slice_digest: str
    dependency_digest: str
    environment_class: str
    test_digest: str

    @property
    def key(self) -> str:
        return stable_digest(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "key": self.key}
