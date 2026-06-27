"""Ω-LEARN-T — Apprentissage de Tristan.

A dependency-free prototype for learning loops grounded by CVCD invariants,
Bayes mastery, M-/M+ memory, curriculum generation, scheduling, persistence,
export, and OAK tests.
"""

from .core import (
    AXES,
    Evidence,
    ErrorRecord,
    LearningEvent,
    LearningProfile,
    LearningState,
    MasteryAxis,
    SkillSpec,
)
from .sage_learning_coach import SageLearningCoach
from .storage import JsonlStore

__all__ = [
    "AXES",
    "Evidence",
    "ErrorRecord",
    "JsonlStore",
    "LearningEvent",
    "LearningProfile",
    "LearningState",
    "MasteryAxis",
    "SageLearningCoach",
    "SkillSpec",
]

__version__ = "0.2.0"
