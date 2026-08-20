from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable


class EvidenceError(ValueError):
    """Raised when capability evidence cannot be evaluated safely."""


@dataclass(frozen=True)
class EvidenceRecord:
    capability_id: str
    evidence_id: str
    method: str
    source_id: str
    reality_level: int = 0
    independent: bool = False
    valid: bool = True

    def __post_init__(self) -> None:
        for field_name in ("capability_id", "evidence_id", "method", "source_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise EvidenceError(f"{field_name} must be a non-empty string")
        if not 0 <= self.reality_level <= 5:
            raise EvidenceError("reality_level must be in [0, 5]")


@dataclass(frozen=True)
class EvidencePolicy:
    min_records: int = 1
    min_distinct_methods: int = 1
    min_independent_sources: int = 0
    min_reality_level: int = 0

    def __post_init__(self) -> None:
        if self.min_records < 1:
            raise EvidenceError("min_records must be >= 1")
        if self.min_distinct_methods < 1:
            raise EvidenceError("min_distinct_methods must be >= 1")
        if self.min_independent_sources < 0:
            raise EvidenceError("min_independent_sources must be >= 0")
        if not 0 <= self.min_reality_level <= 5:
            raise EvidenceError("min_reality_level must be in [0, 5]")


@dataclass(frozen=True)
class CapabilityAssessment:
    capability_id: str
    decision: str
    accepted_evidence_ids: tuple[str, ...]
    distinct_methods: tuple[str, ...]
    independent_sources: tuple[str, ...]
    max_reality_level: int
    unmet_requirements: tuple[str, ...]
    authority: str = "EVIDENCE_ASSESSMENT_ONLY"
    external_action_authorized: bool = False
    credential_awarded: bool = False
    scientific_claim_proven: bool = False

    @property
    def evidence_sufficient(self) -> bool:
        return self.decision == "EVIDENCE_SUFFICIENT_UNDER_POLICY"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_capability(
    records: Iterable[EvidenceRecord],
    policy: EvidencePolicy,
) -> CapabilityAssessment:
    """Evaluate caller-supplied evidence against an explicit deterministic policy.

    This checks structural sufficiency only. It does not independently validate that
    a source is truthful, that a measurement is correct, or that a capability exists
    in the real world.
    """

    rows = tuple(records)
    if not rows:
        raise EvidenceError("at least one evidence record is required")

    capability_ids = {row.capability_id.strip() for row in rows}
    if len(capability_ids) != 1:
        raise EvidenceError("all evidence records must concern one capability")
    capability_id = next(iter(capability_ids))

    seen_ids: set[str] = set()
    accepted: list[EvidenceRecord] = []
    for row in rows:
        evidence_id = row.evidence_id.strip()
        if evidence_id in seen_ids:
            raise EvidenceError(f"duplicate evidence_id: {evidence_id!r}")
        seen_ids.add(evidence_id)
        if row.valid:
            accepted.append(row)

    methods = tuple(sorted({row.method.strip() for row in accepted}))
    independent_sources = tuple(
        sorted({row.source_id.strip() for row in accepted if row.independent})
    )
    max_reality_level = max((row.reality_level for row in accepted), default=0)

    unmet: list[str] = []
    if len(accepted) < policy.min_records:
        unmet.append(f"records<{policy.min_records}")
    if len(methods) < policy.min_distinct_methods:
        unmet.append(f"distinct_methods<{policy.min_distinct_methods}")
    if len(independent_sources) < policy.min_independent_sources:
        unmet.append(f"independent_sources<{policy.min_independent_sources}")
    if max_reality_level < policy.min_reality_level:
        unmet.append(f"reality_level<{policy.min_reality_level}")

    decision = "INSUFFICIENT_EVIDENCE"
    if not unmet:
        decision = "EVIDENCE_SUFFICIENT_UNDER_POLICY"

    return CapabilityAssessment(
        capability_id=capability_id,
        decision=decision,
        accepted_evidence_ids=tuple(sorted(row.evidence_id for row in accepted)),
        distinct_methods=methods,
        independent_sources=independent_sources,
        max_reality_level=max_reality_level,
        unmet_requirements=tuple(unmet),
    )


def make_evidence_receipt(
    assessment: CapabilityAssessment,
    *,
    policy_version: str,
) -> dict[str, object]:
    if not isinstance(policy_version, str) or not policy_version.strip():
        raise EvidenceError("policy_version must be a non-empty string")

    payload = {
        "kind": "omega.university.capability-evidence.r0.2",
        "policy_version": policy_version.strip(),
        "assessment": assessment.to_dict(),
        "boundaries": {
            "policy_sufficiency_is_external_truth": False,
            "evidence_is_credential": False,
            "evidence_is_scientific_proof": False,
            "external_action_authorized": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        **payload,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
