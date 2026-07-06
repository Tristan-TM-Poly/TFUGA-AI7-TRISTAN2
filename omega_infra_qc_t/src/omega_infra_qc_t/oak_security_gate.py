"""OAK security gate for infrastructure publication contexts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

GateStatus = Literal["pass", "review", "block"]


@dataclass(frozen=True)
class SecurityGateResult:
    status: GateStatus
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def publishable(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "publishable": self.publishable,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recommendations": list(self.recommendations),
        }


class OAKSecurityGate:
    """Evaluate if infrastructure outputs can be public."""

    def evaluate_publication_context(
        self,
        *,
        contains_exact_sensitive_location: bool = False,
        contains_access_or_security_details: bool = False,
        contains_personal_data: bool = False,
        contains_realtime_operational_status: bool = False,
        contains_critical_dependency_chain: bool = False,
        source_is_authorized: bool = False,
        human_review_done: bool = False,
        public_safe_redaction_done: bool = False,
        community_context_needed: bool = False,
        community_context_done: bool = False,
    ) -> SecurityGateResult:
        blockers: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        if not source_is_authorized:
            blockers.append("source_not_authorized")
        if contains_exact_sensitive_location:
            blockers.append("exact_sensitive_location")
        if contains_access_or_security_details:
            blockers.append("access_or_security_details")
        if contains_personal_data:
            blockers.append("personal_data")
        if contains_realtime_operational_status:
            blockers.append("realtime_operational_status")
        if contains_critical_dependency_chain:
            blockers.append("critical_dependency_chain")
        if community_context_needed and not community_context_done:
            blockers.append("community_context_missing")
        if not human_review_done:
            warnings.append("human_review_missing")
        if not public_safe_redaction_done:
            warnings.append("redaction_not_confirmed")

        if blockers:
            recommendations.append("restrict_or_redact_before_publication")
            recommendations.append("route_to_authorized_review")
            return SecurityGateResult(status="block", blockers=blockers, warnings=warnings, recommendations=recommendations)

        if warnings:
            recommendations.append("complete_review_before_external_use")
            return SecurityGateResult(status="review", blockers=[], warnings=warnings, recommendations=recommendations)

        recommendations.append("public_safe_summary_only")
        return SecurityGateResult(status="pass", blockers=[], warnings=[], recommendations=recommendations)
