"""Ω-ANIME-EPISODE-T R3 — canonical 20-minute episode compiler."""

from .compiler import EPISODE_ARTIFACT_NAMES, compile_episode_bundle
from .episode import EPISODE_DURATION_S, build_eighth_fire_episode_01_r3

__all__ = [
    "EPISODE_ARTIFACT_NAMES",
    "EPISODE_DURATION_S",
    "build_eighth_fire_episode_01_r3",
    "compile_episode_bundle",
]

__version__ = "3.0.0"
