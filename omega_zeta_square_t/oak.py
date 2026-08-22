"""OAK epistemic guardrails for Ω-ZETA-SQUARE-T∞."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ClaimStatus(str, Enum):
    OBSERVED = "OBSERVED"
    NUMERICALLY_VERIFIED = "NUMERICALLY_VERIFIED"
    SYMBOLICALLY_DERIVED = "SYMBOLICALLY_DERIVED"
    KNOWN_THEOREM = "KNOWN_THEOREM"
    CONJECTURE = "CONJECTURE"
    PROVED = "PROVED"
    REFUTED = "REFUTED"


FORBIDDEN_PROMOTIONS = {
    (ClaimStatus.OBSERVED, ClaimStatus.PROVED),
    (ClaimStatus.NUMERICALLY_VERIFIED, ClaimStatus.PROVED),
    (ClaimStatus.CONJECTURE, ClaimStatus.PROVED),
}


@dataclass(frozen=True)
class OakClaim:
    statement: str
    status: ClaimStatus
    dependencies: tuple[ClaimStatus, ...] = ()
    finite_scope: bool = False
    claims_rh_solution: bool = False


@dataclass(frozen=True)
class OakVerdict:
    admissible: bool
    code: str
    reasons: tuple[str, ...]


def validate_claim(claim: OakClaim) -> OakVerdict:
    """Reject common RH over-promotion patterns.

    This is intentionally conservative. It validates epistemic bookkeeping,
    not mathematical truth.
    """

    reasons = []
    if claim.claims_rh_solution and claim.status is not ClaimStatus.PROVED:
        reasons.append("RH solution claim requires PROVED status")
    if claim.status is ClaimStatus.PROVED:
        weak = [
            dep.value
            for dep in claim.dependencies
            if dep not in {ClaimStatus.PROVED, ClaimStatus.KNOWN_THEOREM}
        ]
        if weak:
            reasons.append("proof depends on non-proof leaves: " + ", ".join(weak))
        if claim.finite_scope and claim.claims_rh_solution:
            reasons.append("finite verification cannot establish the infinite RH quantifier")
    return OakVerdict(
        admissible=not reasons,
        code="PROMOTE" if not reasons else "BLOCK",
        reasons=tuple(reasons),
    )


def validate_transition(source: ClaimStatus, target: ClaimStatus) -> OakVerdict:
    """Validate a direct epistemic status transition."""

    if (source, target) in FORBIDDEN_PROMOTIONS:
        return OakVerdict(False, "BLOCK", (f"forbidden promotion {source.value}->{target.value}",))
    return OakVerdict(True, "PROMOTE", ())


def all_dependencies_proof_grade(statuses: Iterable[ClaimStatus]) -> bool:
    return all(s in {ClaimStatus.PROVED, ClaimStatus.KNOWN_THEOREM} for s in statuses)
