"""Ω-PLASMA-T∞: OAK-safe multi-regime plasma research kernel."""
from .state import PlasmaState, SpeciesState, GeometryState
from .dimensions import PlasmaScales, compute_scales
from .regime_classifier import RegimeAssessment, classify_regime
from .model_compiler import ModelDecision, compile_models
from .oak import OAKReport, audit_state

__all__ = [
    "PlasmaState", "SpeciesState", "GeometryState", "PlasmaScales",
    "compute_scales", "RegimeAssessment", "classify_regime",
    "ModelDecision", "compile_models", "OAKReport", "audit_state",
]
__version__ = "0.1.0"
