"""Negative-memory records for corporate failures and near misses."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass(frozen=True, slots=True)
class MMinusEvent:
    event_id: str
    company_id: str
    category: str
    title: str
    cause: str
    consequence: str
    mitigation: str
    regression_test: str
    severity: str
    recorded_at: str
    resolved: bool = False


def new_event(*, event_id: str, company_id: str, category: str, title: str, cause: str, consequence: str, mitigation: str, regression_test: str, severity: str) -> MMinusEvent:
    return MMinusEvent(event_id, company_id, category, title, cause, consequence, mitigation, regression_test, severity, datetime.now(timezone.utc).isoformat())


class MMinusRegistry:
    def __init__(self, events: list[MMinusEvent] | None = None) -> None:
        self.events = events or []

    def add(self, event: MMinusEvent) -> None:
        if any(item.event_id == event.event_id for item in self.events):
            raise ValueError(f"duplicate_event:{event.event_id}")
        self.events.append(event)

    def open_events(self) -> list[MMinusEvent]:
        return [item for item in self.events if not item.resolved]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([asdict(item) for item in self.events], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
