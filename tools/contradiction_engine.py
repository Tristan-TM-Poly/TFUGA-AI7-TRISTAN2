"""Contradiction Engine for Tristan CanonOS.

Contradictions are treated as fertile audit objects: resolve, separate, test,
deprecate, quarantine, or merge. This module only recommends safe actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ContradictionType(StrEnum):
    LOGICAL = "logical"
    EXPERIMENTAL = "experimental"
    VOCABULARY = "vocabulary"
    REALITY_PROOF_LEVEL = "reality_proof_level"
    METAPHOR_MECHANISM = "metaphor_mechanism"
    AMBITION_PROOF = "ambition_proof"
    SAFETY_AUTOMATION = "safety_automation"


class ContradictionAction(StrEnum):
    RESOLVE = "resolve"
    SEPARATE = "separate"
    DEPRECATE = "deprecate"
    TEST = "test"
    QUARANTINE = "quarantine"
    MERGE = "merge"


@dataclass(frozen=True)
class ContradictionDecision:
    contradiction_type: ContradictionType
    action: ContradictionAction
    rationale: str
    safe_next_action: str


def decide_contradiction_action(
    contradiction_type: ContradictionType,
    *,
    high_risk: bool = False,
    has_test_path: bool = False,
) -> ContradictionDecision:
    if high_risk:
        return ContradictionDecision(
            contradiction_type,
            ContradictionAction.QUARANTINE,
            "High-risk contradiction must not drive external action.",
            "Quarantine and require OAK/human review before mutation.",
        )

    if contradiction_type in {ContradictionType.VOCABULARY, ContradictionType.METAPHOR_MECHANISM}:
        return ContradictionDecision(
            contradiction_type,
            ContradictionAction.SEPARATE,
            "Terms or metaphor/mechanism are conflated.",
            "Split definitions and require RealityAnchor for each meaning.",
        )

    if contradiction_type == ContradictionType.AMBITION_PROOF:
        return ContradictionDecision(
            contradiction_type,
            ContradictionAction.DEPRECATE,
            "Claim strength exceeds evidence.",
            "Downgrade language and add ProofLadder target.",
        )

    if has_test_path or contradiction_type in {ContradictionType.EXPERIMENTAL, ContradictionType.REALITY_PROOF_LEVEL}:
        return ContradictionDecision(
            contradiction_type,
            ContradictionAction.TEST,
            "Contradiction can be made falsifiable.",
            "Create test or benchmark before canon mutation.",
        )

    return ContradictionDecision(
        contradiction_type,
        ContradictionAction.RESOLVE,
        "Low-risk logical contradiction can be resolved in documentation.",
        "Clarify assumptions and update docs in draft branch.",
    )
