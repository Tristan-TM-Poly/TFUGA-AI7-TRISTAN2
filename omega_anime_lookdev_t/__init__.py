"""Ω-ANIME-LOOKDEV-T∞ R5 — original visual-development system."""

from .bible import build_eighth_fire_lookdev_r5
from .compiler import LOOKDEV_ARTIFACT_COUNT, compile_lookdev_bundle
from .models import CharacterDesign, EpisodeLook, LookdevBible, LookdevValidationError

__all__ = [
    "LOOKDEV_ARTIFACT_COUNT",
    "CharacterDesign",
    "EpisodeLook",
    "LookdevBible",
    "LookdevValidationError",
    "build_eighth_fire_lookdev_r5",
    "compile_lookdev_bundle",
]

__version__ = "5.0.0"
