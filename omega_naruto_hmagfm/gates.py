"""Explicit OAK gates for Ω-NARUTO-HMAGFM-HGFMnD².

The gates separate technical ranking from authorization to publish. A proposal
may rank well and still remain blocked or require human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class ProposalView(Protocol):
    status: int
    evidence: Sequence[str]
    provenance: Sequence[str]
    safety_risk: float
    privacy_risk: float
    ip_risk: float


class GateDecision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class GatePolicy:
    """Thresholds and review requirements for public release."""

    safety_threshold: float = 0.25
    privacy_threshold: float = 0.25
    ip_threshold: float = 0.25
    minimum_status: int = 3
    require_evidence: bool = True
    require_provenance: bool = True
    require_human_review: bool = True

    def __post_init__(self) -> None:
        for name, value in {
            "safety_threshold": self.safety_threshold,
            "privacy_threshold": self.privacy_threshold,
            "ip_threshold": self.ip_threshold,
        }.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.minimum_status < 0:
            raise ValueError("minimum_status must be non-negative")


@dataclass(frozen=True)
class GateReport:
    decision: GateDecision
    reasons: tuple[str, ...]
    human_review_required: bool
    release_allowed: bool


def evaluate_publication(
    proposal: ProposalView,
    *,
    policy: GatePolicy | None = None,
    human_review_completed: bool = False,
) -> GateReport:
    """Evaluate whether a proposal may enter a public release path.

    PASS means every configured requirement is satisfied. WARN means the
    content passed automatic checks but still awaits required human review.
    BLOCK means at least one evidence, maturity, privacy, IP, or safety
    condition failed.
    """

    policy = policy or GatePolicy()
    reasons: list[str] = []

    if proposal.safety_risk >= policy.safety_threshold:
        reasons.append("safety gate threshold exceeded")
    if proposal.privacy_risk >= policy.privacy_threshold:
        reasons.append("privacy gate threshold exceeded")
    if proposal.ip_risk >= policy.ip_threshold:
        reasons.append("IP gate threshold exceeded")
    if policy.require_evidence and not proposal.evidence:
        reasons.append("evidence is required")
    if policy.require_provenance and not proposal.provenance:
        reasons.append("provenance is required")
    if int(proposal.status) < policy.minimum_status:
        reasons.append("epistemic status is below the publication floor")

    if reasons:
        return GateReport(
            decision=GateDecision.BLOCK,
            reasons=tuple(reasons),
            human_review_required=policy.require_human_review,
            release_allowed=False,
        )

    if policy.require_human_review and not human_review_completed:
        return GateReport(
            decision=GateDecision.WARN,
            reasons=("human review is still required",),
            human_review_required=True,
            release_allowed=False,
        )

    return GateReport(
        decision=GateDecision.PASS,
        reasons=(),
        human_review_required=policy.require_human_review,
        release_allowed=True,
    )
