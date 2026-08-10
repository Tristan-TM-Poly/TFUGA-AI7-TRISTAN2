from __future__ import annotations

from typing import Mapping, Sequence

from .models import ClaimCoverage, EvidenceValidity, PromotionProof, sorted_unique

_ALLOWED = {
    "FERTILE": {"PROTOTYPED"},
    "HYPOTHESIZED": {"PLANNED"},
    "PLANNED": {"GENERATED"},
    "GENERATED": {"COMPILED"},
    "COMPILED": {"TESTED"},
    "TESTED": {"PROTOTYPED"},
    "PROTOTYPED": {"MEASURED"},
    "SIMULATED": {"MEASURED"},
    "MEASURED": {"REPRODUCED"},
    "REPRODUCED": {"FORMALLY_CHECKED"},
}


class PromotionProofBuilder:
    def build(
        self,
        *,
        claim_id: str,
        from_status: str,
        to_status: str,
        validity: Sequence[EvidenceValidity],
        coverage: ClaimCoverage,
        evidence_bundle_ids: Sequence[str],
        evidence_integrity_verified: bool,
        no_critical_residuals: bool,
        coverage_threshold: float = 0.80,
    ) -> PromotionProof:
        reasons: list[str] = []
        transition_valid = to_status in _ALLOWED.get(from_status, set())
        if not transition_valid:
            reasons.append(f"invalid epistemic transition: {from_status} -> {to_status}")
        current_validity = bool(validity) and all(item.status == "CURRENT" for item in validity)
        if not current_validity:
            reasons.append("all supporting evidence must be CURRENT")
        coverage_ok = coverage.score >= coverage_threshold and not coverage.blocked
        if not coverage_ok:
            reasons.append("claim coverage is below threshold or blocked")
        if not evidence_integrity_verified:
            reasons.append("evidence integrity is not verified")
        if not no_critical_residuals:
            reasons.append("critical residuals remain unresolved")
        if not evidence_bundle_ids:
            reasons.append("at least one evidence bundle is required")
        prerequisites = {
            "transition_valid": transition_valid,
            "evidence_current": current_validity,
            "coverage_sufficient": coverage_ok,
            "evidence_integrity_verified": evidence_integrity_verified,
            "no_critical_residuals": no_critical_residuals,
            "evidence_present": bool(evidence_bundle_ids),
        }
        decision = "ELIGIBLE_FOR_HUMAN_REVIEW" if all(prerequisites.values()) else "BLOCKED"
        return PromotionProof(
            claim_id=claim_id,
            from_status=from_status,
            to_status=to_status,
            evidence_bundle_ids=sorted_unique(evidence_bundle_ids),
            validity_statuses=tuple(item.status for item in validity),
            coverage_score=coverage.score,
            coverage_threshold=coverage_threshold,
            prerequisites=prerequisites,
            decision=decision,
            reasons=tuple(reasons or ["all machine-checkable prerequisites satisfied; human review remains mandatory"]),
        )


class PromotionProofVerifier:
    def verify(self, raw: Mapping[str, object]) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        prerequisites = raw.get("prerequisites", {})
        if not isinstance(prerequisites, Mapping) or not all(bool(value) for value in prerequisites.values()):
            errors.append("all promotion prerequisites must be true")
        if raw.get("decision") != "ELIGIBLE_FOR_HUMAN_REVIEW":
            errors.append("promotion proof is not eligible")
        if raw.get("automatic_merge_allowed") is not False:
            errors.append("automatic merge must remain disabled")
        if raw.get("human_review_required") is not True:
            errors.append("human review must remain required")
        return (not errors, tuple(errors))
