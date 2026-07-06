"""M- memory primitives for Ω-GOV-QC-T.

M- records errors, anti-patterns and blocked patterns as reusable safeguards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

MMinusSeverity = Literal[1, 2, 3, 4, 5]


@dataclass(frozen=True)
class MMinusEvent:
    """A negative-memory event that should become a gate, test or warning."""

    event_id: str
    module: str
    error_type: str
    description: str
    severity: MMinusSeverity = 3
    countermeasure: str = ""
    test_to_add: str = ""
    oak_note: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.event_id.strip():
            errors.append("event_id is required")
        if not self.module.strip():
            errors.append("module is required")
        if not self.error_type.strip():
            errors.append("error_type is required")
        if not self.description.strip():
            errors.append("description is required")
        if not 1 <= int(self.severity) <= 5:
            errors.append("severity must be between 1 and 5")
        if self.severity >= 4 and not self.countermeasure.strip():
            errors.append("severity >= 4 requires a countermeasure")
        return errors

    @property
    def blocks_release(self) -> bool:
        return self.severity >= 5

    @property
    def requires_test(self) -> bool:
        return self.severity >= 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "module": self.module,
            "error_type": self.error_type,
            "description": self.description,
            "severity": self.severity,
            "countermeasure": self.countermeasure,
            "test_to_add": self.test_to_add,
            "oak_note": self.oak_note,
            "blocks_release": self.blocks_release,
            "requires_test": self.requires_test,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class MMinusRegister:
    """Negative-memory register."""

    events: Dict[str, MMinusEvent] = field(default_factory=dict)
    duplicates: List[str] = field(default_factory=list)

    def add(self, event: MMinusEvent) -> None:
        errors = event.validate()
        if errors:
            raise ValueError("Invalid MMinusEvent: " + "; ".join(errors))
        if event.event_id in self.events:
            self.duplicates.append(event.event_id)
            raise ValueError(f"duplicate event_id: {event.event_id}")
        self.events[event.event_id] = event

    def blockers(self) -> List[MMinusEvent]:
        return [event for event in self.events.values() if event.blocks_release]

    def tests_required(self) -> List[MMinusEvent]:
        return [event for event in self.events.values() if event.requires_test]

    def report(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        by_severity: Dict[int, int] = {}
        for event in self.events.values():
            by_type[event.error_type] = by_type.get(event.error_type, 0) + 1
            by_severity[int(event.severity)] = by_severity.get(int(event.severity), 0) + 1
        return {
            "event_count": len(self.events),
            "by_type": by_type,
            "by_severity": by_severity,
            "blockers": [event.event_id for event in self.blockers()],
            "tests_required": [event.event_id for event in self.tests_required()],
            "duplicates": list(self.duplicates),
            "oak_note": "M- turns failures into future gates, tests and countermeasures.",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.m_minus_register.v0",
            "events": [event.to_dict() for event in self.events.values()],
            "report": self.report(),
        }
