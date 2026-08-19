"""Canon Rank classifier for Tristan CanonOS.

Ranks canon objects from C0 raw fragment to C10 fundamental pillar. This is a
conservative maturity label, not a truth oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class CanonRank(IntEnum):
    C0_RAW_FRAGMENT = 0
    C1_CAPTURED_IDEA = 1
    C2_DEFINED_CONCEPT = 2
    C3_TESTABLE_HYPOTHESIS = 3
    C4_STRUCTURED_MODEL = 4
    C5_PROTOTYPE = 5
    C6_TESTED_TOOL = 6
    C7_BENCHMARKED = 7
    C8_REPRODUCED = 8
    C9_REINFORCED_CANON = 9
    C10_FUNDAMENTAL_PILLAR = 10


@dataclass(frozen=True)
class CanonRankAssessment:
    rank: CanonRank
    label: str
    reasons: tuple[str, ...]
    next_upgrade: str


def assess_canon_rank(
    *,
    captured: bool = False,
    defined: bool = False,
    testable: bool = False,
    structured_model: bool = False,
    prototype: bool = False,
    tested_tool: bool = False,
    benchmarked: bool = False,
    reproduced: bool = False,
    reinforced: bool = False,
    fundamental: bool = False,
) -> CanonRankAssessment:
    reasons: list[str] = []

    if fundamental and reinforced and reproduced:
        rank = CanonRank.C10_FUNDAMENTAL_PILLAR
        reasons.append("fundamental_reinforced_reproduced")
    elif reinforced:
        rank = CanonRank.C9_REINFORCED_CANON
        reasons.append("reinforced_canon")
    elif reproduced:
        rank = CanonRank.C8_REPRODUCED
        reasons.append("reproduced")
    elif benchmarked:
        rank = CanonRank.C7_BENCHMARKED
        reasons.append("benchmarked")
    elif tested_tool:
        rank = CanonRank.C6_TESTED_TOOL
        reasons.append("tested_tool")
    elif prototype:
        rank = CanonRank.C5_PROTOTYPE
        reasons.append("prototype")
    elif structured_model:
        rank = CanonRank.C4_STRUCTURED_MODEL
        reasons.append("structured_model")
    elif testable:
        rank = CanonRank.C3_TESTABLE_HYPOTHESIS
        reasons.append("testable")
    elif defined:
        rank = CanonRank.C2_DEFINED_CONCEPT
        reasons.append("defined")
    elif captured:
        rank = CanonRank.C1_CAPTURED_IDEA
        reasons.append("captured")
    else:
        rank = CanonRank.C0_RAW_FRAGMENT
        reasons.append("raw_fragment")

    labels = {
        CanonRank.C0_RAW_FRAGMENT: "raw fragment",
        CanonRank.C1_CAPTURED_IDEA: "captured idea",
        CanonRank.C2_DEFINED_CONCEPT: "defined concept",
        CanonRank.C3_TESTABLE_HYPOTHESIS: "testable hypothesis",
        CanonRank.C4_STRUCTURED_MODEL: "structured model",
        CanonRank.C5_PROTOTYPE: "prototype",
        CanonRank.C6_TESTED_TOOL: "tested tool",
        CanonRank.C7_BENCHMARKED: "benchmarked",
        CanonRank.C8_REPRODUCED: "reproduced",
        CanonRank.C9_REINFORCED_CANON: "reinforced canon",
        CanonRank.C10_FUNDAMENTAL_PILLAR: "fundamental pillar",
    }

    nexts = {
        CanonRank.C0_RAW_FRAGMENT: "capture and define the idea",
        CanonRank.C1_CAPTURED_IDEA: "define terms and boundaries",
        CanonRank.C2_DEFINED_CONCEPT: "make it testable",
        CanonRank.C3_TESTABLE_HYPOTHESIS: "structure the model",
        CanonRank.C4_STRUCTURED_MODEL: "build prototype",
        CanonRank.C5_PROTOTYPE: "add tests",
        CanonRank.C6_TESTED_TOOL: "benchmark",
        CanonRank.C7_BENCHMARKED: "seek reproduction",
        CanonRank.C8_REPRODUCED: "canon review",
        CanonRank.C9_REINFORCED_CANON: "evaluate if fundamental",
        CanonRank.C10_FUNDAMENTAL_PILLAR: "maintain regression and scope",
    }

    return CanonRankAssessment(rank, labels[rank], tuple(reasons), nexts[rank])
