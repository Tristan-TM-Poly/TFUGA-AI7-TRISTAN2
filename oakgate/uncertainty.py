"""Transparent U² confidence-debt heuristics for OAKGate."""

from __future__ import annotations

from dataclasses import dataclass

from .model import Claim, EpistemicStatus


_STATUS_CONFIDENCE_CAP = {
    EpistemicStatus.MYTH: 0.25,
    EpistemicStatus.CONCEPT: 0.40,
    EpistemicStatus.FORMALIZATION: 0.70,
    EpistemicStatus.SIMULATION: 0.78,
    EpistemicStatus.PROTOTYPE: 0.82,
    EpistemicStatus.EMPIRICAL: 0.88,
    EpistemicStatus.REPRODUCED: 0.94,
    EpistemicStatus.CERTIFIED: 0.97,
    EpistemicStatus.DEPLOYED: 0.95,
}


@dataclass(frozen=True)
class ConfidenceAssessment:
    claimed: float
    justified: float
    debt: float
    status_cap: float

    @property
    def fragile(self) -> bool:
        return self.debt >= 0.25


def assess_confidence(claim: Claim) -> ConfidenceAssessment:
    """Estimate confidence debt without pretending to calibrate scientific truth.

    The cap is a policy heuristic tied to the declared epistemic status. Evidence
    and artifact omissions reduce the cap. It is intentionally conservative and
    must not be presented as an empirical probability of truth.
    """

    cap = _STATUS_CONFIDENCE_CAP[claim.status]
    if claim.status.rank >= EpistemicStatus.FORMALIZATION.rank and not claim.evidence:
        cap -= 0.25
    if claim.status.rank >= EpistemicStatus.PROTOTYPE.rank and not claim.artifacts:
        cap -= 0.20
    if claim.source_attributions and not claim.evidence:
        cap -= 0.15

    justified = min(claim.claimed_confidence, max(0.0, cap))
    debt = max(0.0, claim.claimed_confidence - justified)
    return ConfidenceAssessment(
        claimed=claim.claimed_confidence,
        justified=justified,
        debt=debt,
        status_cap=max(0.0, cap),
    )
