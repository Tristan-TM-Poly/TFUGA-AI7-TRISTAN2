"""Core primitives for Ω-GAME-T.

This module deliberately stays small and dependency-free. It models a playable
world as a lightweight hypergraph: entities, binary relations, hyperedges,
rules, events, and quality metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class Entity:
    """A node in the Ω-GAME-T world graph."""

    entity_id: str
    kind: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Event:
    """A proposed or accepted world transition."""

    event_id: str
    kind: str
    description: str
    actors: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorldGraph:
    """Minimal hypergraph representation of a playable world.

    - entities are graph nodes;
    - relations are typed edges;
    - hyperedges bind many entities into quests, factions, economies or systems;
    - memory stores world traces, residues and consequences.
    """

    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    hyperedges: dict[str, set[str]] = field(default_factory=dict)
    rules: list[str] = field(default_factory=list)
    memory: list[dict[str, Any]] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        if entity.entity_id in self.entities:
            raise ValueError(f"Entity already exists: {entity.entity_id}")
        self.entities[entity.entity_id] = entity

    def add_relation(self, source: str, relation: str, target: str) -> None:
        self._require_entity(source)
        self._require_entity(target)
        self.relations.append((source, relation, target))

    def add_hyperedge(self, hyperedge_id: str, entity_ids: set[str]) -> None:
        for entity_id in entity_ids:
            self._require_entity(entity_id)
        self.hyperedges[hyperedge_id] = set(entity_ids)

    def remember(self, entry: dict[str, Any]) -> None:
        self.memory.append(entry)

    def _require_entity(self, entity_id: str) -> None:
        if entity_id not in self.entities:
            raise KeyError(f"Unknown entity: {entity_id}")

    def snapshot(self) -> dict[str, Any]:
        return {
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "hyperedge_count": len(self.hyperedges),
            "rule_count": len(self.rules),
            "memory_count": len(self.memory),
            "entity_kinds": sorted({entity.kind for entity in self.entities.values()}),
        }


Rule = Callable[[WorldGraph, Event], tuple[bool, str]]


@dataclass(slots=True)
class RuleKernel:
    """Small rule system used before OAK accepts a world event."""

    rules: list[Rule] = field(default_factory=list)

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def evaluate(self, world: WorldGraph, event: Event) -> tuple[bool, list[str]]:
        failures: list[str] = []
        for rule in self.rules:
            passed, reason = rule(world, event)
            if not passed:
                failures.append(reason)
        return not failures, failures


@dataclass(slots=True)
class GameQualityScore:
    """Composite benchmark for Ω-GAME-OAK.

    Values are expected between 0 and 1. Exploits and friction are penalties.
    """

    fun: float = 0.5
    agency: float = 0.5
    coherence: float = 0.5
    novelty: float = 0.5
    fairness: float = 0.5
    learning: float = 0.5
    friction: float = 0.0
    exploits: float = 0.0

    def composite(self) -> float:
        positive = (
            self.fun
            + self.agency
            + self.coherence
            + self.novelty
            + self.fairness
            + self.learning
        ) / 6.0
        penalty = (self.friction + self.exploits) / 2.0
        return max(0.0, min(1.0, positive - 0.5 * penalty))
