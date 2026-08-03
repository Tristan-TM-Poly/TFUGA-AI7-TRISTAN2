"""Typed design-bible objects and measurable look-development invariants."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any


_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class LookdevValidationError(ValueError):
    """Raised when the visual bible violates an R5 invariant."""


def _required(value: str, location: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location}: non-empty text required")


@dataclass(frozen=True)
class CharacterDesign:
    character_id: str
    name: str
    role: str
    silhouette_signature: str
    shape_language: str
    body_ratio: str
    palette: tuple[str, ...]
    accent_color: str
    motion_rules: tuple[str, ...]
    expressions: tuple[str, ...]
    voice_register: str
    voice_tempo: str
    voice_boundary: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        for field in (
            "character_id", "name", "role", "silhouette_signature",
            "shape_language", "body_ratio", "voice_register", "voice_tempo",
            "voice_boundary",
        ):
            _required(str(getattr(self, field)), f"character.{self.character_id}.{field}", errors)
        if len(self.palette) != 5 or any(not _HEX.match(color) for color in self.palette):
            errors.append(f"character.{self.character_id}.palette: five hex colors required")
        if not _HEX.match(self.accent_color):
            errors.append(f"character.{self.character_id}.accent_color: invalid hex")
        if len(self.motion_rules) < 3:
            errors.append(f"character.{self.character_id}.motion_rules: at least three required")
        if len(self.expressions) != 6:
            errors.append(f"character.{self.character_id}.expressions: exactly six required")
        return errors


@dataclass(frozen=True)
class EpisodeLook:
    episode_number: int
    title: str
    phase: str
    palette: tuple[str, ...]
    light_key: str
    composition_rule: str
    forbidden_composition: str
    visual_motif: str
    emotional_curve: tuple[float, ...]
    target_contrast_ratio: float
    camera_entropy_target: float

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not 1 <= self.episode_number <= 12:
            errors.append("episode_number: must be in [1, 12]")
        for field in (
            "title", "phase", "light_key", "composition_rule",
            "forbidden_composition", "visual_motif",
        ):
            _required(str(getattr(self, field)), f"episode.{self.episode_number}.{field}", errors)
        if len(self.palette) != 6 or any(not _HEX.match(color) for color in self.palette):
            errors.append(f"episode.{self.episode_number}.palette: six hex colors required")
        if len(self.emotional_curve) != 6:
            errors.append(f"episode.{self.episode_number}.emotional_curve: six beats required")
        if any(not 0.0 <= value <= 1.0 for value in self.emotional_curve):
            errors.append(f"episode.{self.episode_number}.emotional_curve: values must be in [0, 1]")
        if self.target_contrast_ratio < 4.5:
            errors.append(f"episode.{self.episode_number}.target_contrast_ratio: must be >= 4.5")
        if not 0.0 <= self.camera_entropy_target <= 1.0:
            errors.append(f"episode.{self.episode_number}.camera_entropy_target: must be in [0, 1]")
        return errors


@dataclass(frozen=True)
class LookdevBible:
    project_id: str
    style_id: str
    style_name: str
    version: str
    publication_state: str
    originality_statement: str
    global_invariants: tuple[str, ...]
    forbidden_defaults: tuple[str, ...]
    characters: tuple[CharacterDesign, ...]
    episodes: tuple[EpisodeLook, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        for field in (
            "project_id", "style_id", "style_name", "version",
            "publication_state", "originality_statement",
        ):
            _required(str(getattr(self, field)), f"lookdev.{field}", errors)
        if self.version != "omega-anime-lookdev/r5":
            errors.append("lookdev.version: expected omega-anime-lookdev/r5")
        if self.publication_state != "private-draft":
            errors.append("lookdev.publication_state: must remain private-draft")
        if len(self.global_invariants) < 8:
            errors.append("lookdev.global_invariants: at least eight required")
        if len(self.forbidden_defaults) < 6:
            errors.append("lookdev.forbidden_defaults: at least six required")
        if len(self.characters) != 4:
            errors.append("lookdev.characters: exactly four design anchors required")
        if len(self.episodes) != 12:
            errors.append("lookdev.episodes: exactly twelve required")
        for character in self.characters:
            errors.extend(character.validate())
        for episode in self.episodes:
            errors.extend(episode.validate())
        if len({character.character_id for character in self.characters}) != len(self.characters):
            errors.append("lookdev.characters: duplicate ids")
        if len({character.silhouette_signature for character in self.characters}) != len(self.characters):
            errors.append("lookdev.characters: silhouettes must be unique")
        if [episode.episode_number for episode in self.episodes] != list(range(1, 13)):
            errors.append("lookdev.episodes: order must be contiguous")
        if len({episode.title for episode in self.episodes}) != 12:
            errors.append("lookdev.episodes: titles must be unique")
        if len({episode.composition_rule for episode in self.episodes}) < 8:
            errors.append("lookdev.episodes: insufficient composition diversity")
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise LookdevValidationError("\n".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))
