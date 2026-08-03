"""Ω-ANIME-SEASON-T∞ R4 — deterministic 12×20-minute season compiler."""

from .compiler import (
    EPISODE_ARTIFACT_NAMES,
    SEASON_ROOT_ARTIFACT_NAMES,
    compile_season_bundle,
)
from .models import EpisodeBlueprint, SeasonEpisode, SeasonPlan, SeasonValidationError
from .season import (
    EPISODE_DURATION_S,
    SEASON_DURATION_S,
    build_eighth_fire_season_01_r4,
)

__all__ = [
    "EPISODE_ARTIFACT_NAMES",
    "SEASON_ROOT_ARTIFACT_NAMES",
    "EPISODE_DURATION_S",
    "SEASON_DURATION_S",
    "EpisodeBlueprint",
    "SeasonEpisode",
    "SeasonPlan",
    "SeasonValidationError",
    "build_eighth_fire_season_01_r4",
    "compile_season_bundle",
]

__version__ = "4.0.0"
