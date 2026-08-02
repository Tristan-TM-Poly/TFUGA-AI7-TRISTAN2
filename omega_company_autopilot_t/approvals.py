"""Content-bound approval records."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .hashing import sha256_object
from .models import ActionRequest, ApprovalRecord


def action_hash(action: ActionRequest) -> str:
    return sha256_object(action)


def approve_action(action: ActionRequest, *, approval_id: str, approver: str, reason: str, valid_hours: int = 24) -> ApprovalRecord:
    now = datetime.now(timezone.utc)
    return ApprovalRecord(
        approval_id=approval_id,
        action_id=action.action_id,
        approver=approver,
        decision="APPROVE",
        action_hash=action_hash(action),
        reason=reason,
        approved_at=now.isoformat(),
        expires_at=(now + timedelta(hours=valid_hours)).isoformat(),
    )


def valid_approvals(action: ActionRequest, approvals: list[ApprovalRecord], *, now: datetime | None = None) -> list[ApprovalRecord]:
    current_hash = action_hash(action)
    now = now or datetime.now(timezone.utc)
    valid: list[ApprovalRecord] = []
    seen_approvers: set[str] = set()
    for approval in approvals:
        if approval.action_id != action.action_id or approval.action_hash != current_hash:
            continue
        if approval.decision != "APPROVE" or approval.approver in seen_approvers:
            continue
        if approval.expires_at and datetime.fromisoformat(approval.expires_at) < now:
            continue
        valid.append(approval)
        seen_approvers.add(approval.approver)
    return valid
