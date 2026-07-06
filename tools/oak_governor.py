"""OAK Governor for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

OAK redirects propulsion rather than stopping it. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OAKSignal(StrEnum):
    SAFE = "safe"
    UNCERTAIN = "uncertain"
    WEAK_PROOF = "weak_proof"
    PUBLIC_REVIEW = "public_review"
    PRIVATE_REVIEW = "private_review"
    IRREVERSIBLE = "irreversible"
    HIGH_RISK = "high_risk"


@dataclass(frozen=True)
class OAKGovernanceDecision:
    signal: OAKSignal
    route: str
    artifact: str


ROUTES = {
    OAKSignal.SAFE: ("continue", "draft_pr"),
    OAKSignal.UNCERTAIN: ("simulate", "simulation"),
    OAKSignal.WEAK_PROOF: ("test", "test"),
    OAKSignal.PUBLIC_REVIEW: ("review", "review_packet"),
    OAKSignal.PRIVATE_REVIEW: ("private_note", "private_note"),
    OAKSignal.IRREVERSIBLE: ("hold", "review_dossier"),
    OAKSignal.HIGH_RISK: ("quarantine", "m_minus"),
}


def govern_oak(signal: OAKSignal) -> OAKGovernanceDecision:
    route, artifact = ROUTES[signal]
    return OAKGovernanceDecision(signal, route, artifact)
