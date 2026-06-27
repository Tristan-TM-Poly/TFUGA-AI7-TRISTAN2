"""Ω-LEARN-T — Apprentissage de Tristan.

A small, dependency-free prototype for learning loops grounded by
CVCD invariants, Bayes mastery, M-/M+ memory, curriculum generation, and OAK tests.
"""

from .core import (
    AXES,
    Evidence,
    LearningProfile,
    LearningState,
    MasteryAxis,
    SkillSpec,
)
from .sage_learning_coach import SageLearningCoach

__all__ = [
    "AXES",
    "Evidence",
    "LearningProfile",
    "LearningState",
    "MasteryAxis",
    "SageLearningCoach",
    "SkillSpec",
]

__version__ = "0.1.0"
