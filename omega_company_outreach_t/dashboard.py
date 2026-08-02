from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .models import OutreachCase, OutreachStatus, PublicMailEvent
from .policy import next_action_for_event


@dataclass(frozen=True, slots=True)
class Dashboard:
    generated_at: str
    totals: dict[str, int]
    by_company: dict[str, int]
    by_status: dict[str, int]
    reply_classes: dict[str, int]
    next_actions: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "totals": self.totals,
            "by_company": self.by_company,
            "by_status": self.by_status,
            "reply_classes": self.reply_classes,
            "next_actions": self.next_actions,
        }

    def as_markdown(self) -> str:
        lines = [
            "# Ω Company Outreach Dashboard",
            "",
            f"Generated: `{self.generated_at}`",
            "",
            f"- Cases: **{self.totals.get('cases', 0)}**",
            f"- Events: **{self.totals.get('events', 0)}**",
            f"- Open cases: **{self.totals.get('open_cases', 0)}**",
            "",
            "## By company",
        ]
        lines.extend(f"- `{key}`: {value}" for key, value in sorted(self.by_company.items()))
        lines.append("")
        lines.append("## Next actions")
        lines.extend(f"- `{key}`: {value}" for key, value in sorted(self.next_actions.items()))
        return "\n".join(lines) + "\n"


def build_dashboard(
    cases: Iterable[OutreachCase],
    events: Iterable[PublicMailEvent],
    *,
    generated_at: str | None = None,
) -> Dashboard:
    cases_list = list(cases)
    events_list = list(events)
    by_company = Counter(case.company_unit.value for case in cases_list)
    by_status = Counter(case.status.value for case in cases_list)
    reply_classes = Counter(
        event.reply_class.value for event in events_list if event.reply_class is not None
    )
    next_actions = Counter(
        next_action_for_event(event).value for event in events_list
        if event.event_type.value in {"reply", "auto_reply", "bounce", "unsubscribe"}
    )
    open_cases = sum(
        case.status not in {OutreachStatus.CLOSED, OutreachStatus.BLOCKED}
        for case in cases_list
    )
    return Dashboard(
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
        totals={"cases": len(cases_list), "events": len(events_list), "open_cases": open_cases},
        by_company=dict(by_company),
        by_status=dict(by_status),
        reply_classes=dict(reply_classes),
        next_actions=dict(next_actions),
    )
