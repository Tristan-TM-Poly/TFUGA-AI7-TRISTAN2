"""Reality Gradient classifier for Tristan AIT Reality Forge.

Classifies ideas from R0 intuition to R10 proof/standard. This is not a truth
oracle; it is a conservative status labeler to prevent hype and vision/proof
confusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class RealityLevel(IntEnum):
    R0_INTUITION = 0
    R1_VISION = 1
    R2_METAPHOR = 2
    R3_HYPOTHESIS = 3
    R4_FORMAL_MODEL = 4
    R5_PROTOTYPE = 5
    R6_LOCAL_TEST = 6
    R7_MEASUREMENT = 7
    R8_REPRODUCTION = 8
    R9_REINFORCED_CANON = 9
    R10_PROOF_OR_STANDARD = 10


@dataclass(frozen=True)
class RealityAssessment:
    level: RealityLevel
    label: str
    reasons: tuple[str, ...]
    allowed_language: str
    next_upgrade: str


def assess_reality_level(
    *,
    has_clear_definition: bool = False,
    has_metaphor_only: bool = False,
    has_testable_claim: bool = False,
    has_formal_model: bool = False,
    has_prototype: bool = False,
    has_local_test: bool = False,
    has_measurement: bool = False,
    has_reproduction: bool = False,
    canon_reviewed: bool = False,
    standard_or_proof: bool = False,
) -> RealityAssessment:
    """Assess the Reality Gradient level of an idea."""

    reasons: list[str] = []

    if standard_or_proof and has_reproduction and has_measurement:
        level = RealityLevel.R10_PROOF_OR_STANDARD
        reasons.append("standard_or_proof_with_reproduction_and_measurement")
    elif canon_reviewed and has_reproduction:
        level = RealityLevel.R9_REINFORCED_CANON
        reasons.append("canon_reviewed_and_reproduced")
    elif has_reproduction:
        level = RealityLevel.R8_REPRODUCTION
        reasons.append("independent_or_repeated_reproduction")
    elif has_measurement:
        level = RealityLevel.R7_MEASUREMENT
        reasons.append("measured_result")
    elif has_local_test:
        level = RealityLevel.R6_LOCAL_TEST
        reasons.append("local_test_exists")
    elif has_prototype:
        level = RealityLevel.R5_PROTOTYPE
        reasons.append("prototype_exists")
    elif has_formal_model:
        level = RealityLevel.R4_FORMAL_MODEL
        reasons.append("formal_model_exists")
    elif has_testable_claim:
        level = RealityLevel.R3_HYPOTHESIS
        reasons.append("testable_claim_exists")
    elif has_metaphor_only or has_clear_definition:
        level = RealityLevel.R2_METAPHOR
        reasons.append("metaphor_or_defined_concept_without_test")
    else:
        level = RealityLevel.R1_VISION
        reasons.append("unanchored_or_early_vision")

    language = {
        RealityLevel.R0_INTUITION: "intuition only",
        RealityLevel.R1_VISION: "vision / exploratory idea",
        RealityLevel.R2_METAPHOR: "metaphor or conceptual framing",
        RealityLevel.R3_HYPOTHESIS: "testable hypothesis",
        RealityLevel.R4_FORMAL_MODEL: "formal model candidate",
        RealityLevel.R5_PROTOTYPE: "prototype candidate",
        RealityLevel.R6_LOCAL_TEST: "locally tested result",
        RealityLevel.R7_MEASUREMENT: "measured result with limits",
        RealityLevel.R8_REPRODUCTION: "reproduced result",
        RealityLevel.R9_REINFORCED_CANON: "reinforced canon",
        RealityLevel.R10_PROOF_OR_STANDARD: "proof/standard within stated scope",
    }[level]

    next_upgrade = {
        RealityLevel.R1_VISION: "add definition, example, risk, and RealityAnchor",
        RealityLevel.R2_METAPHOR: "separate metaphor from mechanism and add a falsifiable test",
        RealityLevel.R3_HYPOTHESIS: "build formal model or minimal prototype",
        RealityLevel.R4_FORMAL_MODEL: "implement prototype",
        RealityLevel.R5_PROTOTYPE: "add local tests",
        RealityLevel.R6_LOCAL_TEST: "add measurement metrics",
        RealityLevel.R7_MEASUREMENT: "seek reproduction",
        RealityLevel.R8_REPRODUCTION: "canon review and stress tests",
        RealityLevel.R9_REINFORCED_CANON: "standardize or prove within scope",
        RealityLevel.R10_PROOF_OR_STANDARD: "maintain scope, citations, and regression tests",
        RealityLevel.R0_INTUITION: "write the intuition as a vision",
    }[level]

    return RealityAssessment(level, language, tuple(reasons), language, next_upgrade)


def forbid_overclaim(level: RealityLevel, claimed_level: RealityLevel) -> bool:
    """Return True when language claims a stronger level than evidence supports."""

    return int(claimed_level) > int(level)
