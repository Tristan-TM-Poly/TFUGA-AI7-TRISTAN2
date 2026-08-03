"""Approval state machine for sovereign action review."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_EDIT = "needs_edit"
    NEEDS_REVIEW = "needs_review"
    EXPIRED = "expired"


ALLOWED_TRANSITIONS: dict[ApprovalState, set[ApprovalState]] = {
    ApprovalState.PENDING: {
        ApprovalState.APPROVED,
        ApprovalState.REJECTED,
        ApprovalState.NEEDS_EDIT,
        ApprovalState.NEEDS_REVIEW,
        ApprovalState.EXPIRED,
    },
    ApprovalState.NEEDS_EDIT: {ApprovalState.PENDING, ApprovalState.REJECTED, ApprovalState.EXPIRED},
    ApprovalState.NEEDS_REVIEW: {ApprovalState.PENDING, ApprovalState.REJECTED, ApprovalState.EXPIRED},
    ApprovalState.APPROVED: {ApprovalState.EXPIRED},
    ApprovalState.REJECTED: set(),
    ApprovalState.EXPIRED: set(),
}


@dataclass(frozen=True)
class ApprovalDecision:
    state: ApprovalState
    reason: str
    reviewer: str = "tristan"
    notes: list[str] = field(default_factory=list)

    def transition_to(self, new_state: ApprovalState, reason: str, reviewer: str = "tristan") -> "ApprovalDecision":
        if new_state not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid approval transition: {self.state.value} -> {new_state.value}")
        return ApprovalDecision(
            state=new_state,
            reason=reason,
            reviewer=reviewer,
            notes=[*self.notes, f"{self.state.value}->{new_state.value}: {reason}"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "reason": self.reason,
            "reviewer": self.reviewer,
            "notes": list(self.notes),
        }
