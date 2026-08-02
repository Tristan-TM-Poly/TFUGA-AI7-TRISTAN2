"""Typed timeline objects and OAK invariants for the R2 animatic."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


class TimelineValidationError(ValueError):
    """Raised when an animatic timeline violates a structural invariant."""


def _text(value: str, location: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location}: non-empty text required")


@dataclass(frozen=True)
class AnimaticShot:
    shot_id: str
    scene_id: str
    order: int
    start_s: float
    end_s: float
    duration_s: float
    purpose: str
    framing: str
    camera_motion: str
    subjects: tuple[str, ...]
    caption: str
    dialogue: str
    audio_cue: str
    intensity: float

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in (
            "shot_id",
            "scene_id",
            "purpose",
            "framing",
            "camera_motion",
            "caption",
            "audio_cue",
        ):
            _text(str(getattr(self, name)), f"shot.{self.shot_id}.{name}", errors)
        if self.order < 1:
            errors.append(f"shot.{self.shot_id}.order: must be >= 1")
        if self.start_s < 0:
            errors.append(f"shot.{self.shot_id}.start_s: cannot be negative")
        if self.end_s <= self.start_s:
            errors.append(f"shot.{self.shot_id}.end_s: must exceed start_s")
        if self.duration_s <= 0:
            errors.append(f"shot.{self.shot_id}.duration_s: must be positive")
        if abs((self.end_s - self.start_s) - self.duration_s) > 1e-6:
            errors.append(f"shot.{self.shot_id}: duration does not match interval")
        if not self.subjects:
            errors.append(f"shot.{self.shot_id}.subjects: at least one required")
        if not 0.0 <= self.intensity <= 1.0:
            errors.append(f"shot.{self.shot_id}.intensity: must be in [0, 1]")
        return errors


@dataclass(frozen=True)
class AnimaticScene:
    scene_id: str
    title: str
    order: int
    start_s: float
    end_s: float
    duration_s: float
    objective: str
    irreversible_change: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("scene_id", "title", "objective", "irreversible_change"):
            _text(str(getattr(self, name)), f"scene.{self.scene_id}.{name}", errors)
        if self.order < 1:
            errors.append(f"scene.{self.scene_id}.order: must be >= 1")
        if self.start_s < 0 or self.end_s <= self.start_s:
            errors.append(f"scene.{self.scene_id}: invalid time interval")
        if abs((self.end_s - self.start_s) - self.duration_s) > 1e-6:
            errors.append(f"scene.{self.scene_id}: duration does not match interval")
        return errors


@dataclass(frozen=True)
class AnimaticTimeline:
    project_id: str
    title: str
    version: str
    duration_s: float
    fps_reference: int
    publication_state: str
    scenes: tuple[AnimaticScene, ...]
    shots: tuple[AnimaticShot, ...]
    disclaimers: tuple[str, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("project_id", "title", "version", "publication_state"):
            _text(str(getattr(self, name)), f"timeline.{name}", errors)
        if self.duration_s <= 0:
            errors.append("timeline.duration_s: must be positive")
        if self.fps_reference < 1:
            errors.append("timeline.fps_reference: must be positive")
        if not self.scenes:
            errors.append("timeline.scenes: at least one scene required")
        if not self.shots:
            errors.append("timeline.shots: at least one shot required")
        if not self.disclaimers:
            errors.append("timeline.disclaimers: OAK boundary required")

        for scene in self.scenes:
            errors.extend(scene.validate())
        for shot in self.shots:
            errors.extend(shot.validate())

        scene_ids = {scene.scene_id for scene in self.scenes}
        unknown = {shot.scene_id for shot in self.shots} - scene_ids
        if unknown:
            errors.append(f"timeline.shots: unknown scene ids {sorted(unknown)}")

        scene_orders = [scene.order for scene in self.scenes]
        if scene_orders != list(range(1, len(self.scenes) + 1)):
            errors.append("timeline.scenes: order must be contiguous")

        ordered = sorted(self.shots, key=lambda item: (item.start_s, item.scene_id, item.order))
        cursor = 0.0
        for shot in ordered:
            if abs(shot.start_s - cursor) > 1e-6:
                errors.append(
                    f"shot.{shot.shot_id}: gap or overlap at {cursor:.3f}s -> {shot.start_s:.3f}s"
                )
            cursor = shot.end_s
        if abs(cursor - self.duration_s) > 1e-6:
            errors.append(f"timeline: final end {cursor:.3f}s != duration {self.duration_s:.3f}s")

        for scene in self.scenes:
            scene_shots = [shot for shot in ordered if shot.scene_id == scene.scene_id]
            if not scene_shots:
                errors.append(f"scene.{scene.scene_id}: no shots")
                continue
            orders = [shot.order for shot in scene_shots]
            if orders != list(range(1, len(scene_shots) + 1)):
                errors.append(f"scene.{scene.scene_id}: shot order must be contiguous")
            if abs(scene_shots[0].start_s - scene.start_s) > 1e-6:
                errors.append(f"scene.{scene.scene_id}: first shot start mismatch")
            if abs(scene_shots[-1].end_s - scene.end_s) > 1e-6:
                errors.append(f"scene.{scene.scene_id}: final shot end mismatch")
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise TimelineValidationError("\n".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
