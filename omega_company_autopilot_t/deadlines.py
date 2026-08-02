"""Deadline planning without claiming to discover legal obligations automatically."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from .models import DeadlineEvent, Obligation

DEFAULT_OFFSETS = (-90, -60, -30, -14, -7, -1, 0)
_ACTIONS = {
    -90: ("INFO", "prepare_scope"),
    -60: ("INFO", "collect_evidence"),
    -30: ("WARNING", "run_oak_validation"),
    -14: ("WARNING", "request_human_approval"),
    -7: ("HIGH", "escalate"),
    -1: ("CRITICAL", "block_conflicting_risk_actions"),
    0: ("DUE", "submit_or_record_human_completion"),
}


class DeadlineEngine:
    def schedule(self, obligation: Obligation, offsets: Iterable[int] = DEFAULT_OFFSETS) -> list[DeadlineEvent]:
        events: list[DeadlineEvent] = []
        for offset in sorted(set(offsets)):
            severity, action = _ACTIONS.get(offset, ("INFO", "review"))
            events.append(DeadlineEvent(obligation.obligation_id, obligation.due_date + timedelta(days=offset), offset, severity, action))
        return events

    def upcoming(self, obligations: Iterable[Obligation], *, today: date, horizon_days: int = 120) -> list[tuple[Obligation, int]]:
        result: list[tuple[Obligation, int]] = []
        for obligation in obligations:
            if obligation.completed:
                continue
            days = (obligation.due_date - today).days
            if days <= horizon_days:
                result.append((obligation, days))
        return sorted(result, key=lambda item: (item[1], item[0].obligation_id))
