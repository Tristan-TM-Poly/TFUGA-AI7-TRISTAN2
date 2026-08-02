"""Deterministic follow-up planning without background execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from .models import CaseRecord, DeliveryReceipt


@dataclass(frozen=True, slots=True)
class FollowUpAction:
    case_id: str
    due_at: str
    condition: str
    action: str
    autonomous: bool

    def to_dict(self) -> dict:
        return asdict(self)


def schedule_followups(case: CaseRecord, receipt: DeliveryReceipt) -> list[FollowUpAction]:
    now = datetime.now(timezone.utc)
    actions = [
        FollowUpAction(case.case_id, (now + timedelta(days=1)).isoformat(), "provider_not_accepted", "verify_channel_status", True),
        FollowUpAction(case.case_id, (now + timedelta(days=3)).isoformat(), "recipient_not_confirmed", "prepare_follow_up_draft", False),
        FollowUpAction(case.case_id, (now + timedelta(days=7)).isoformat(), "case_unresolved", "escalate_to_founder", False),
        FollowUpAction(case.case_id, (now + timedelta(days=30)).isoformat(), "case_completed", "apply_retention_or_archive_policy", False),
    ]
    if receipt.status == "DRY_RUN_PREPARED":
        actions.insert(0, FollowUpAction(case.case_id, now.isoformat(), "dispatch_not_executed", "request_dispatch_decision", False))
    return actions
