"""Ω-ANIME-T∞: OAK-safe narrative and anime preproduction kernel."""

from .engine import NarrativeLinter, build_eighth_fire_project, compile_project_bundle
from .models import (
    AnimeProject,
    CharacterState,
    EpisodeBeat,
    NarrativePromise,
    OakStatus,
    ProjectValidationError,
)

__all__ = [
    "AnimeProject",
    "CharacterState",
    "EpisodeBeat",
    "NarrativeLinter",
    "NarrativePromise",
    "OakStatus",
    "ProjectValidationError",
    "build_eighth_fire_project",
    "compile_project_bundle",
]

__version__ = "0.1.0"
