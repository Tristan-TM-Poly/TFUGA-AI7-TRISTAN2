from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .core import LearningEvent, SkillSpec


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class JsonlStore:
    """Tiny zero-dependency JSONL persistence layer."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.events_path = self.root / "events.jsonl"
        self.skills_path = self.root / "skills.jsonl"

    def init(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_path.touch(exist_ok=True)
        self.skills_path.touch(exist_ok=True)

    def append_jsonl(self, path: Path, payload: Dict[str, Any]) -> None:
        self.init()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def append_event(self, event_type: str, skill: str, payload: Dict[str, Any]) -> LearningEvent:
        event = LearningEvent(event_type=event_type, skill=skill, payload=payload, timestamp=utc_now())
        self.append_jsonl(self.events_path, event.to_dict())
        return event

    def save_skill(self, spec: SkillSpec) -> None:
        payload = {"timestamp": utc_now(), **spec.to_dict()}
        self.append_jsonl(self.skills_path, payload)

    def read_jsonl(self, path: Path) -> List[dict]:
        if not path.exists():
            return []
        rows: List[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def events(self) -> List[LearningEvent]:
        return [LearningEvent.from_mapping(row) for row in self.read_jsonl(self.events_path)]

    def skills(self) -> List[dict]:
        return self.read_jsonl(self.skills_path)

    def status(self) -> dict:
        events = self.read_jsonl(self.events_path)
        skills = self.read_jsonl(self.skills_path)
        by_type: Dict[str, int] = {}
        by_skill: Dict[str, int] = {}
        for event in events:
            by_type[event.get("event_type", "event")] = by_type.get(event.get("event_type", "event"), 0) + 1
            by_skill[event.get("skill", "")] = by_skill.get(event.get("skill", ""), 0) + 1
        return {
            "root": str(self.root),
            "skills_logged": len(skills),
            "events_logged": len(events),
            "events_by_type": by_type,
            "events_by_skill": by_skill,
        }
