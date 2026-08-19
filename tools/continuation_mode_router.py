"""Continuation Mode Router for Ω-AIT-NO-HUMAN-BOTTLENECK-T.

The router prevents routine human bottlenecks by selecting the safest productive
mode. It plans and creates safe artifacts; it does not bypass review gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ContinuationMode(StrEnum):
    CREATE = "create"
    SIMULATE = "simulate"
    REVIEW = "review"
    HOLD = "hold"


class SafeArtifact(StrEnum):
    DOC = "doc"
    SCHEMA = "schema"
    TOOL = "tool"
    TEST = "test"
    REPORT = "report"
    DRAFT_PR = "draft_pr"
    SIMULATION = "simulation"
    NOTE = "note"
    PACKET = "packet"
    M_MINUS = "m_minus"


@dataclass(frozen=True)
class ContinuationDecision:
    mode: ContinuationMode
    level: int
    artifact: SafeArtifact
    reason: str
    next_safe_action: str


def route_continuation(
    *,
    reversible: bool = True,
    private: bool = True,
    testable: bool = True,
    review_domain: bool = False,
    public_effect: bool = False,
    irreversible: bool = False,
) -> ContinuationDecision:
    """Route work to the strongest safe continuation mode."""

    if irreversible or review_domain:
        return ContinuationDecision(
            ContinuationMode.HOLD,
            10,
            SafeArtifact.PACKET,
            "Review threshold reached; direct execution is not the safe next step.",
            "Create review packet, OAK report, tests, and a safe next-option note.",
        )

    if public_effect:
        return ContinuationDecision(
            ContinuationMode.REVIEW,
            6,
            SafeArtifact.DRAFT_PR,
            "Public-facing effect requires review gate.",
            "Prepare draft PR or review packet; do not publish or merge automatically.",
        )

    if reversible and private and testable:
        return ContinuationDecision(
            ContinuationMode.CREATE,
            5,
            SafeArtifact.DRAFT_PR,
            "Work is reversible, private, and testable.",
            "Continue with branch, files, tests, and draft PR without routine human bottleneck.",
        )

    return ContinuationDecision(
        ContinuationMode.SIMULATE,
        2,
        SafeArtifact.SIMULATION,
        "Some safety property is missing.",
        "Run dry simulation, add missing tests/evidence, and produce an OAK report.",
    )
