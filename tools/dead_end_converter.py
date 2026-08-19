"""Dead-End Converter for Ω-AIT-CONTINUATION-ENGINE-T.

A dead-end is only a change of action level. This module maps common blockers to
safe artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DeadEndType(StrEnum):
    NO_PERMISSION = "no_permission"
    NO_PROOF = "no_proof"
    NO_TEST = "no_test"
    NO_DATA = "no_data"
    NO_BENCHMARK = "no_benchmark"
    NO_SOURCE = "no_source"
    NO_SAFETY = "no_safety"
    NO_ROLLBACK = "no_rollback"
    NO_CLARITY = "no_clarity"
    NO_AUTHORIZED_DECISION = "no_authorized_decision"


@dataclass(frozen=True)
class DeadEndConversion:
    dead_end: DeadEndType
    safe_artifact: str
    safe_action: str


CONVERSIONS = {
    DeadEndType.NO_PERMISSION: ("draft_only", "Create a draft artifact without external effect."),
    DeadEndType.NO_PROOF: ("test", "Create falsification test or toy example."),
    DeadEndType.NO_TEST: ("test_skeleton", "Create minimal test skeleton."),
    DeadEndType.NO_DATA: ("synthetic_fixture", "Create synthetic fixture or simulation."),
    DeadEndType.NO_BENCHMARK: ("simple_baseline", "Create simple baseline benchmark."),
    DeadEndType.NO_SOURCE: ("source_status_note", "Create source request/status note."),
    DeadEndType.NO_SAFETY: ("oak_report", "Create OAK report before implementation."),
    DeadEndType.NO_ROLLBACK: ("rollback_plan", "Create rollback or compensation plan."),
    DeadEndType.NO_CLARITY: ("reality_anchor", "Create RealityAnchor and scope note."),
    DeadEndType.NO_AUTHORIZED_DECISION: ("review_packet", "Create review packet and safe options."),
}


def convert_dead_end(dead_end: DeadEndType) -> DeadEndConversion:
    artifact, action = CONVERSIONS[dead_end]
    return DeadEndConversion(dead_end, artifact, action)
