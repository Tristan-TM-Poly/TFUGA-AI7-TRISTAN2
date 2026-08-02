"""Domain models for Ω-ANIME-T∞ R0.1.

The module deliberately uses only the Python standard library so the first
prototype remains portable, auditable and easy to test.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OakStatus(str, Enum):
    EXPLORATORY = "EXPLORATORY"
    FORMALIZED = "FORMALIZED"
    SIMULATED = "SIMULATED"
    DEMONSTRATED = "DEMONSTRATED"
    REPLICATED = "REPLICATED"
    CANONICAL = "CANONICAL"


class ProjectValidationError(ValueError):
    """Raised when a project violates a blocking OAK rule."""


def _json_ready(value: Any) -> Any:
    """Recursively convert immutable model containers to JSON-native values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value


@dataclass(frozen=True)
class CharacterState:
    character_id: str
    name: str
    desire: str
    need: str
    fear: str
    contradiction: str
    power: str
    limitation: str
    knowledge: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        required = {
            "character_id": self.character_id,
            "name": self.name,
            "desire": self.desire,
            "need": self.need,
            "fear": self.fear,
            "contradiction": self.contradiction,
            "power": self.power,
            "limitation": self.limitation,
        }
        for key, value in required.items():
            if not value.strip():
                errors.append(f"character.{self.character_id}.{key}: required")
        if self.power.strip() and not self.limitation.strip():
            errors.append(f"character.{self.character_id}: power requires limitation")
        return errors


@dataclass(frozen=True)
class NarrativePromise:
    promise_id: str
    introduced_in: str
    setup: str
    expected_payoff: str
    status: str = "OPEN"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.status not in {"OPEN", "PARTIAL", "RESOLVED", "ABANDONED"}:
            errors.append(f"promise.{self.promise_id}: invalid status {self.status!r}")
        if not self.setup.strip():
            errors.append(f"promise.{self.promise_id}.setup: required")
        if self.status != "ABANDONED" and not self.expected_payoff.strip():
            errors.append(f"promise.{self.promise_id}.expected_payoff: required")
        return errors


@dataclass(frozen=True)
class EpisodeBeat:
    beat_id: str
    order: int
    title: str
    objective: str
    conflict: str
    irreversible_change: str
    information_revealed: tuple[str, ...] = ()
    estimated_seconds: int = 30

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.order < 1:
            errors.append(f"beat.{self.beat_id}.order: must be >= 1")
        if self.estimated_seconds < 1:
            errors.append(f"beat.{self.beat_id}.estimated_seconds: must be >= 1")
        if not self.objective.strip():
            errors.append(f"beat.{self.beat_id}.objective: required")
        if not self.conflict.strip():
            errors.append(f"beat.{self.beat_id}.conflict: required")
        if not self.irreversible_change.strip():
            errors.append(f"beat.{self.beat_id}.irreversible_change: required")
        return errors


@dataclass(frozen=True)
class AnimeProject:
    project_id: str
    title: str
    logline: str
    theme_question: str
    audience: str
    format_name: str
    target_duration_seconds: int
    visual_invariants: tuple[str, ...]
    world_rules: tuple[str, ...]
    characters: tuple[CharacterState, ...]
    episode_beats: tuple[EpisodeBeat, ...]
    promises: tuple[NarrativePromise, ...]
    oak_status: OakStatus = OakStatus.FORMALIZED
    evidence: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.project_id.strip():
            errors.append("project_id: required")
        if not self.title.strip():
            errors.append("title: required")
        if len(self.logline.strip()) < 20:
            errors.append("logline: must contain at least 20 characters")
        if not self.theme_question.strip().endswith("?"):
            errors.append("theme_question: must be an explicit question")
        if self.target_duration_seconds < 30:
            errors.append("target_duration_seconds: must be >= 30")
        if not self.visual_invariants:
            errors.append("visual_invariants: at least one invariant is required")
        if len(self.world_rules) < 3:
            errors.append("world_rules: at least three rules are required")
        if not self.characters:
            errors.append("characters: at least one character is required")
        if not self.episode_beats:
            errors.append("episode_beats: at least one beat is required")

        for character in self.characters:
            errors.extend(character.validate())
        for promise in self.promises:
            errors.extend(promise.validate())
        for beat in self.episode_beats:
            errors.extend(beat.validate())

        character_ids = [character.character_id for character in self.characters]
        if len(character_ids) != len(set(character_ids)):
            errors.append("characters: duplicate character_id")

        beat_ids = [beat.beat_id for beat in self.episode_beats]
        if len(beat_ids) != len(set(beat_ids)):
            errors.append("episode_beats: duplicate beat_id")
        orders = [beat.order for beat in self.episode_beats]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            errors.append("episode_beats: order must be unique and ascending")

        promised_seconds = sum(beat.estimated_seconds for beat in self.episode_beats)
        tolerance = max(15, int(self.target_duration_seconds * 0.10))
        if abs(promised_seconds - self.target_duration_seconds) > tolerance:
            errors.append(
                "episode_beats: estimated duration differs from target by more than 10%"
            )

        if self.oak_status in {OakStatus.DEMONSTRATED, OakStatus.REPLICATED, OakStatus.CANONICAL}:
            if not self.evidence:
                errors.append(f"oak_status.{self.oak_status.value}: evidence is required")
        if self.oak_status in {OakStatus.REPLICATED, OakStatus.CANONICAL}:
            if not any("independent" in item.lower() for item in self.evidence):
                errors.append(f"oak_status.{self.oak_status.value}: independent evidence required")
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise ProjectValidationError("\n".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))
