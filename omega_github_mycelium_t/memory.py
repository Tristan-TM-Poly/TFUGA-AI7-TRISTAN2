from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import canonical_json, sha256_digest


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    event_id: str
    polarity: str
    event_type: str
    subject: str
    lesson: str
    prevention_rule: str
    source_refs: tuple[str, ...]
    previous_hash: str | None
    event_hash: str
    metadata: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        polarity: str,
        event_type: str,
        subject: str,
        lesson: str,
        prevention_rule: str,
        source_refs: Iterable[str] = (),
        previous_hash: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "MemoryEvent":
        if polarity not in {"m_plus", "m_minus"}:
            raise ValueError("polarity must be m_plus or m_minus")
        payload = {
            "polarity": polarity,
            "event_type": event_type,
            "subject": subject,
            "lesson": lesson,
            "prevention_rule": prevention_rule,
            "source_refs": tuple(source_refs),
            "previous_hash": previous_hash,
            "metadata": dict(metadata or {}),
        }
        event_hash = sha256_digest(payload)
        return cls(
            event_id=f"memory.{event_hash[:20]}",
            event_hash=event_hash,
            **payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryLedger:
    def __init__(self, events: Iterable[MemoryEvent] = ()) -> None:
        self._events: list[MemoryEvent] = []
        for event in events:
            self.append_existing(event)

    @property
    def events(self) -> tuple[MemoryEvent, ...]:
        return tuple(self._events)

    def append(
        self,
        *,
        polarity: str,
        event_type: str,
        subject: str,
        lesson: str,
        prevention_rule: str,
        source_refs: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> MemoryEvent:
        event = MemoryEvent.create(
            polarity=polarity,
            event_type=event_type,
            subject=subject,
            lesson=lesson,
            prevention_rule=prevention_rule,
            source_refs=source_refs,
            previous_hash=self._events[-1].event_hash if self._events else None,
            metadata=metadata,
        )
        self._events.append(event)
        return event

    def append_existing(self, event: MemoryEvent) -> None:
        expected_previous = self._events[-1].event_hash if self._events else None
        if event.previous_hash != expected_previous:
            raise ValueError("memory hash chain is not contiguous")
        recreated = MemoryEvent.create(
            polarity=event.polarity,
            event_type=event.event_type,
            subject=event.subject,
            lesson=event.lesson,
            prevention_rule=event.prevention_rule,
            source_refs=event.source_refs,
            previous_hash=event.previous_hash,
            metadata=event.metadata,
        )
        if recreated.event_hash != event.event_hash or recreated.event_id != event.event_id:
            raise ValueError("memory event digest mismatch")
        self._events.append(event)

    def verify(self) -> bool:
        try:
            MemoryLedger(self._events)
        except ValueError:
            return False
        return True

    def write_jsonl(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = "".join(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for event in self._events)
        destination.write_text(text, encoding="utf-8")
        return destination
