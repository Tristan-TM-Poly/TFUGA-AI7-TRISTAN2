"""Ω-PARTICULES-CHAMPS-T∞ executable research kernel.

The package separates established physics, effective models, exploratory
hypotheses, simulations, detector reconstructions, and evidence status.
"""
from .core import (
    EpistemicStatus, OntologyLevel, SpinClass, EvidenceRef, FieldSpec,
    ParticleSpec, InteractionSpec, ModelRegistry, ValidationIssue,
)
from .physics import FourVector, TwoBodyEvent, qed_emu_event, two_flavor_probability
from .pipeline import OmegaPCTPipeline, PipelineReport
from .oak import OAKGate, OAKReport

__all__ = [
    "EpistemicStatus", "OntologyLevel", "SpinClass", "EvidenceRef",
    "FieldSpec", "ParticleSpec", "InteractionSpec", "ModelRegistry",
    "ValidationIssue", "FourVector", "TwoBodyEvent", "qed_emu_event",
    "two_flavor_probability", "OmegaPCTPipeline", "PipelineReport",
    "OAKGate", "OAKReport",
]
__version__ = "0.2.0"
