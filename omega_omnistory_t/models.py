"""Typed core models for Ω-OMNISTORY-T∞ R6.

R6 treats manga/anime as projections of a versioned causal StoryIR.  It is
standard-library only and intentionally separates generation, judgement,
canon promotion and regeneration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CanonStatus(str, Enum):
    DRAFT = "DRAFT"
    POSSIBLE = "POSSIBLE"
    CANON = "CANON"
    RETCON = "RETCON"
    DEPRECATED = "DEPRECATED"
    CONTRADICTED = "CONTRADICTED"


class EvidenceLevel(str, Enum):
    GENERATED = "GENERATED"
    CHECKED = "CHECKED"
    BENCHMARKED = "BENCHMARKED"
    HUMAN_APPROVED = "HUMAN_APPROVED"


class PromotionDecision(str, Enum):
    PROMOTE = "PROMOTE"
    KEEP_EXPERIMENTAL = "KEEP_EXPERIMENTAL"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    DEPRECATE = "DEPRECATE"
    DESTROY = "DESTROY"


class OmnistoryValidationError(ValueError):
    pass


def _ready(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _ready(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_ready(v) for v in value]
    return value


@dataclass(frozen=True)
class CharacterGenome:
    character_id: str
    name: str
    goals: tuple[str, ...]
    fears: tuple[str, ...]
    knowledge: tuple[str, ...] = ()
    abilities: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    voice_rules: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.character_id.strip(): errors.append("character_id: required")
        if not self.name.strip(): errors.append(f"character.{self.character_id}.name: required")
        if not self.goals: errors.append(f"character.{self.character_id}.goals: required")
        if self.abilities and not self.constraints:
            errors.append(f"character.{self.character_id}: abilities require constraints")
        return errors


@dataclass(frozen=True)
class CausalEvent:
    event_id: str
    summary: str
    causes: tuple[str, ...] = ()
    actors: tuple[str, ...] = ()
    consequences: tuple[str, ...] = ()
    irreversible: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.event_id.strip(): errors.append("event.event_id: required")
        if not self.summary.strip(): errors.append(f"event.{self.event_id}.summary: required")
        if self.event_id in self.causes: errors.append(f"event.{self.event_id}: cannot cause itself")
        return errors


@dataclass(frozen=True)
class CanonFact:
    fact_id: str
    statement: str
    status: CanonStatus = CanonStatus.DRAFT
    provenance: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.fact_id.strip(): errors.append("fact.fact_id: required")
        if not self.statement.strip(): errors.append(f"fact.{self.fact_id}.statement: required")
        if self.status in {CanonStatus.CANON, CanonStatus.RETCON} and not self.provenance:
            errors.append(f"fact.{self.fact_id}: canon/retcon requires provenance")
        return errors


@dataclass(frozen=True)
class NarrativeResidual:
    residual_id: str
    domain: str
    scale: str
    description: str
    severity: int
    evidence: tuple[str, ...] = ()
    proposed_generator: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not 1 <= self.severity <= 5:
            errors.append(f"residual.{self.residual_id}.severity: must be 1..5")
        if not self.description.strip(): errors.append(f"residual.{self.residual_id}.description: required")
        return errors


@dataclass(frozen=True)
class GeneratorSpec:
    generator_id: str
    purpose: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    verifier_ids: tuple[str, ...]
    cost_units: int = 1
    experimental: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.generator_id.strip(): errors.append("generator.generator_id: required")
        if not self.purpose.strip(): errors.append(f"generator.{self.generator_id}.purpose: required")
        if not self.inputs or not self.outputs: errors.append(f"generator.{self.generator_id}: inputs/outputs required")
        if self.generator_id in self.verifier_ids:
            errors.append(f"generator.{self.generator_id}: Generator != Judge")
        if self.cost_units < 1: errors.append(f"generator.{self.generator_id}.cost_units: must be >= 1")
        return errors


@dataclass(frozen=True)
class Crystal:
    crystal_id: str
    capability: str
    implementation: str
    evidence: tuple[str, ...]
    benchmarks: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    known_failures: tuple[str, ...] = ()
    limits: tuple[str, ...] = ()
    rollback: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.evidence: errors.append(f"crystal.{self.crystal_id}.evidence: required")
        if not self.benchmarks: errors.append(f"crystal.{self.crystal_id}.benchmarks: required")
        if not self.rollback.strip(): errors.append(f"crystal.{self.crystal_id}.rollback: required")
        return errors


@dataclass(frozen=True)
class StoryIR:
    story_id: str
    title: str
    premise: str
    theme_question: str
    world_rules: tuple[str, ...]
    characters: tuple[CharacterGenome, ...]
    events: tuple[CausalEvent, ...]
    canon: tuple[CanonFact, ...]
    residuals: tuple[NarrativeResidual, ...] = ()
    presentation_backends: tuple[str, ...] = ("manga", "anime")
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.story_id.strip(): errors.append("story_id: required")
        if not self.title.strip(): errors.append("title: required")
        if len(self.premise.strip()) < 20: errors.append("premise: must contain >= 20 characters")
        if not self.theme_question.strip().endswith("?"): errors.append("theme_question: must end with ?")
        if len(self.world_rules) < 3: errors.append("world_rules: at least three rules required")
        if not self.characters: errors.append("characters: at least one required")
        if not self.events: errors.append("events: at least one required")
        for value in self.characters: errors.extend(value.validate())
        for value in self.events: errors.extend(value.validate())
        for value in self.canon: errors.extend(value.validate())
        for value in self.residuals: errors.extend(value.validate())
        ids = [c.character_id for c in self.characters]
        if len(ids) != len(set(ids)): errors.append("characters: duplicate character_id")
        event_ids = [e.event_id for e in self.events]
        if len(event_ids) != len(set(event_ids)): errors.append("events: duplicate event_id")
        event_set = set(event_ids)
        character_set = set(ids)
        for event in self.events:
            missing_causes = set(event.causes) - event_set
            if missing_causes: errors.append(f"event.{event.event_id}: unknown causes {sorted(missing_causes)}")
            missing_actors = set(event.actors) - character_set
            if missing_actors: errors.append(f"event.{event.event_id}: unknown actors {sorted(missing_actors)}")
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors: raise OmnistoryValidationError("\n".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return _ready(asdict(self))
