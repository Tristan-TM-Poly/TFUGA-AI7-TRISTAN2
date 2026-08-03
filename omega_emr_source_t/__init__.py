"""Ω-EMR-SOURCE-T∞: OAK-safe electromagnetic source synthesis kernel."""

from .atlas import MECHANISMS, mechanism_atlas, search_mechanisms
from .classifier import SpectralClassification, classify_frequency
from .compiler import compile_source
from .models import (
    Mechanism,
    MechanismCandidate,
    SourcePlan,
    SpectrumTarget,
)
from .oak import OAKReport, audit_plan
from .safety import SafetyAssessment, assess_safety

__all__ = [
    "MECHANISMS",
    "Mechanism",
    "MechanismCandidate",
    "OAKReport",
    "SafetyAssessment",
    "SourcePlan",
    "SpectralClassification",
    "SpectrumTarget",
    "assess_safety",
    "audit_plan",
    "classify_frequency",
    "compile_source",
    "mechanism_atlas",
    "search_mechanisms",
]

__version__ = "0.1.0"
