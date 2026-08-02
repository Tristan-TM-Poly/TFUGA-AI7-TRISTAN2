"""Ω-ANIME-ANIMATIC-T R2 — deterministic low-fidelity animatic compiler."""

from .compiler import ARTIFACT_NAMES, compile_animatic_bundle
from .models import AnimaticScene, AnimaticShot, AnimaticTimeline, TimelineValidationError
from .timeline import build_eighth_fire_animatic_r2

__all__ = [
    "ARTIFACT_NAMES",
    "AnimaticScene",
    "AnimaticShot",
    "AnimaticTimeline",
    "TimelineValidationError",
    "build_eighth_fire_animatic_r2",
    "compile_animatic_bundle",
]
