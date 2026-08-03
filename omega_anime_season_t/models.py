"""Typed season objects and cross-episode OAK invariants."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from omega_anime_animatic_t.models import AnimaticTimeline


class SeasonValidationError(ValueError):
    """Raised when a season violates duration, continuity or causal-debt gates."""


@dataclass(frozen=True)
class EpisodeBlueprint:
    number: int
    title: str
    phase: str
    location: str
    logline: str
    primary_question: str
    entry_condition: str
    irreversible_change: str
    debt_opened: str
    debt_closed: str
    hook: str
    motifs: tuple[str, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not 1 <= self.number <= 12:
            errors.append(f"episode.{self.number}.number: must be in [1, 12]")
        for name in (
            "title",
            "phase",
            "location",
            "logline",
            "primary_question",
            "entry_condition",
            "irreversible_change",
            "debt_opened",
            "hook",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"episode.{self.number}.{name}: non-empty text required")
        if len(self.motifs) < 6:
            errors.append(f"episode.{self.number}.motifs: at least six motifs required")
        return errors


@dataclass(frozen=True)
class SeasonEpisode:
    blueprint: EpisodeBlueprint
    timeline: AnimaticTimeline

    def validate(self) -> list[str]:
        errors = self.blueprint.validate() + self.timeline.validate()
        if self.timeline.duration_s != 1200.0:
            errors.append(f"episode.{self.blueprint.number}.duration: expected 1200 seconds")
        if len(self.timeline.scenes) != 12:
            errors.append(f"episode.{self.blueprint.number}.scenes: expected 12")
        if len(self.timeline.shots) != 114:
            errors.append(f"episode.{self.blueprint.number}.shots: expected 114")
        return errors

    def summary(self) -> dict[str, Any]:
        data = asdict(self.blueprint)
        data.update(
            {
                "duration_s": self.timeline.duration_s,
                "scene_count": len(self.timeline.scenes),
                "shot_count": len(self.timeline.shots),
                "project_id": self.timeline.project_id,
            }
        )
        return json.loads(json.dumps(data, ensure_ascii=False))


@dataclass(frozen=True)
class SeasonPlan:
    season_id: str
    title: str
    version: str
    publication_state: str
    episodes: tuple[SeasonEpisode, ...]
    disclaimers: tuple[str, ...]

    @property
    def total_duration_s(self) -> float:
        return sum(episode.timeline.duration_s for episode in self.episodes)

    @property
    def total_scenes(self) -> int:
        return sum(len(episode.timeline.scenes) for episode in self.episodes)

    @property
    def total_shots(self) -> int:
        return sum(len(episode.timeline.shots) for episode in self.episodes)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.version != "omega-anime-season/r4":
            errors.append("season.version: expected omega-anime-season/r4")
        if self.publication_state != "private-draft":
            errors.append("season.publication_state: must remain private-draft")
        if len(self.episodes) != 12:
            errors.append("season.episodes: expected 12")
        if [episode.blueprint.number for episode in self.episodes] != list(range(1, 13)):
            errors.append("season.episodes: numbers must be contiguous from 1 to 12")
        for episode in self.episodes:
            errors.extend(episode.validate())
        if self.total_duration_s != 14_400.0:
            errors.append(f"season.duration: expected 14400, got {self.total_duration_s}")
        if self.total_scenes != 144:
            errors.append(f"season.scenes: expected 144, got {self.total_scenes}")
        if self.total_shots != 1_368:
            errors.append(f"season.shots: expected 1368, got {self.total_shots}")
        if len({episode.blueprint.title for episode in self.episodes}) != 12:
            errors.append("season.titles: episode titles must be unique")
        if len({episode.timeline.project_id for episode in self.episodes}) != 12:
            errors.append("season.project_ids: timeline ids must be unique")

        known_debts: set[str] = set()
        for index, episode in enumerate(self.episodes):
            blueprint = episode.blueprint
            if blueprint.debt_closed and blueprint.debt_closed not in known_debts:
                errors.append(
                    f"episode.{blueprint.number}: closes unknown debt {blueprint.debt_closed}"
                )
            if blueprint.debt_closed:
                known_debts.remove(blueprint.debt_closed)
            if blueprint.debt_opened in known_debts:
                errors.append(
                    f"episode.{blueprint.number}: reopens active debt {blueprint.debt_opened}"
                )
            known_debts.add(blueprint.debt_opened)
            if index + 1 < len(self.episodes):
                next_blueprint = self.episodes[index + 1].blueprint
                if blueprint.hook != next_blueprint.entry_condition:
                    errors.append(
                        f"episode.{blueprint.number}->{next_blueprint.number}: hook/entry mismatch"
                    )
        if known_debts != {"DEBT-SEASON2-001"}:
            errors.append(f"season.debts: expected only DEBT-SEASON2-001 open, got {known_debts}")
        if len(self.disclaimers) < 4:
            errors.append("season.disclaimers: at least four OAK boundaries required")
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise SeasonValidationError("\n".join(errors))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "season_id": self.season_id,
            "title": self.title,
            "version": self.version,
            "publication_state": self.publication_state,
            "episode_count": len(self.episodes),
            "total_duration_s": self.total_duration_s,
            "total_scenes": self.total_scenes,
            "total_shots": self.total_shots,
            "episodes": [episode.summary() for episode in self.episodes],
            "disclaimers": list(self.disclaimers),
        }
        return json.loads(json.dumps(payload, ensure_ascii=False))
