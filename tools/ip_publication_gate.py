"""Review Release Gate for Ω-AIT-RESEARCH-FACTORY-T.

Classifies whether an asset should remain private/internal, become a technical
note, or move to reviewed release planning. It does not publish anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReleaseStatus(StrEnum):
    PRIVATE_INTERNAL = "private_internal"
    NEEDS_REVIEW = "needs_review"
    TECHNICAL_NOTE = "technical_note"
    OPEN_RELEASE_CANDIDATE = "open_release_candidate"
    HOLD = "hold"


@dataclass(frozen=True)
class ReleaseGateDecision:
    status: ReleaseStatus
    reason: str
    required_gates: tuple[str, ...]
    safe_next_action: str


def decide_release_status(
    *,
    sensitive_content: bool = False,
    unclear_ownership: bool = False,
    has_sources: bool = False,
    has_tests: bool = False,
    public_goal: bool = False,
) -> ReleaseGateDecision:
    gates: list[str] = ["oak"]

    if sensitive_content or unclear_ownership:
        gates.extend(["privacy_review", "asset_review"])
        return ReleaseGateDecision(
            ReleaseStatus.HOLD,
            "Sensitive or ownership-unclear material cannot be released.",
            tuple(gates),
            "Keep internal and run review gates.",
        )

    if public_goal and not (has_sources and has_tests):
        gates.extend(["sources", "tests"])
        return ReleaseGateDecision(
            ReleaseStatus.NEEDS_REVIEW,
            "Public-facing work needs sources and tests first.",
            tuple(gates),
            "Prepare technical draft and add sources/tests.",
        )

    if public_goal:
        return ReleaseGateDecision(
            ReleaseStatus.OPEN_RELEASE_CANDIDATE,
            "Sources and tests exist for a reviewed release candidate.",
            tuple(gates),
            "Prepare draft PR and release notes; do not auto-publish.",
        )

    return ReleaseGateDecision(
        ReleaseStatus.TECHNICAL_NOTE if has_tests else ReleaseStatus.PRIVATE_INTERNAL,
        "Internal or technical-note path is appropriate.",
        tuple(gates),
        "Keep as internal note or draft artifact.",
    )
