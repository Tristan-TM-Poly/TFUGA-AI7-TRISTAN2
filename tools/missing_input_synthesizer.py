"""Missing Input Synthesizer for Ω-AIT-CONTINUATION-ENGINE-T.

Missing inputs become assumptions, uncertainty, safe defaults, and tests to
reduce uncertainty. Missing information is not a stop condition.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class UncertaintyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class MissingInputPlan:
    missing_input: str
    assumptions: tuple[str, ...]
    uncertainty: UncertaintyLevel
    safe_default: str
    test_to_reduce_uncertainty: str
    artifact_to_continue: str


def synthesize_missing_input(
    missing_input: str,
    *,
    high_impact: bool = False,
    has_reasonable_default: bool = True,
) -> MissingInputPlan:
    if high_impact:
        return MissingInputPlan(
            missing_input,
            assumptions=("do_not_execute_direct_action", "use_review_packet"),
            uncertainty=UncertaintyLevel.HIGH,
            safe_default="hold direct action and create review packet",
            test_to_reduce_uncertainty="define expert/review checklist or small offline test",
            artifact_to_continue="review_packet",
        )

    if has_reasonable_default:
        return MissingInputPlan(
            missing_input,
            assumptions=("use conservative default", "mark uncertainty explicitly"),
            uncertainty=UncertaintyLevel.MEDIUM,
            safe_default=f"conservative default for {missing_input}",
            test_to_reduce_uncertainty="add toy test or synthetic fixture",
            artifact_to_continue="test_or_simulation",
        )

    return MissingInputPlan(
        missing_input,
        assumptions=("insufficient context",),
        uncertainty=UncertaintyLevel.HIGH,
        safe_default="create clarification note without external action",
        test_to_reduce_uncertainty="collect minimal safe context or create assumptions table",
        artifact_to_continue="assumptions_note",
    )
