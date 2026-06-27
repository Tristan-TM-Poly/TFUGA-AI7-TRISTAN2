from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Entity:
    entity_id: str
    kind: str
    traits: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    event_id: str
    actor_id: str
    action: str
    target_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GameQualityScore:
    agency: float
    fairness: float
    coherence: float
    testability: float
    safety: float

    def normalized(self) -> "GameQualityScore":
        return GameQualityScore(*(_clamp01(value) for value in self.to_list()))

    def to_list(self) -> list[float]:
        return [self.agency, self.fairness, self.coherence, self.testability, self.safety]

    @property
    def mean(self) -> float:
        values = self.normalized().to_list()
        return round(sum(values) / len(values), 4)

    def to_dict(self) -> dict[str, float]:
        normalized = self.normalized()
        return {
            "agency": normalized.agency,
            "fairness": normalized.fairness,
            "coherence": normalized.coherence,
            "testability": normalized.testability,
            "safety": normalized.safety,
            "mean": normalized.mean,
        }


@dataclass
class WorldGraph:
    world_id: str
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        if entity.entity_id in self.entities:
            raise ValueError(f"duplicate entity_id: {entity.entity_id}")
        self.entities[entity.entity_id] = entity

    def add_event(self, event: Event) -> None:
        if event.actor_id not in self.entities:
            raise ValueError(f"unknown actor_id: {event.actor_id}")
        if event.target_id is not None and event.target_id not in self.entities:
            raise ValueError(f"unknown target_id: {event.target_id}")
        self.events.append(event)

    def quality_score(self) -> GameQualityScore:
        entity_count = max(1, len(self.entities))
        event_count = len(self.events)
        actor_diversity = len({event.actor_id for event in self.events}) / entity_count
        target_validity = 1.0 if all(event.target_id is None or event.target_id in self.entities for event in self.events) else 0.0
        agency = min(1.0, actor_diversity + 0.25)
        fairness = 1.0 if event_count == 0 else max(0.0, min(1.0, actor_diversity))
        coherence = target_validity
        testability = 1.0 if self.world_id and entity_count > 0 else 0.0
        safety = 1.0
        return GameQualityScore(agency, fairness, coherence, testability, safety).normalized()

    def to_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "events": [asdict(event) for event in self.events],
            "quality_score": self.quality_score().to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"


@dataclass(frozen=True)
class RuleKernel:
    allowed_actions: tuple[str, ...]
    required_actor_kinds: tuple[str, ...] = ()

    def validate_event(self, world: WorldGraph, event: Event) -> list[str]:
        errors: list[str] = []
        actor = world.entities.get(event.actor_id)
        if actor is None:
            errors.append("unknown_actor")
        elif self.required_actor_kinds and actor.kind not in self.required_actor_kinds:
            errors.append("actor_kind_not_allowed")
        if event.action not in self.allowed_actions:
            errors.append("action_not_allowed")
        if event.target_id is not None and event.target_id not in world.entities:
            errors.append("unknown_target")
        return errors


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
