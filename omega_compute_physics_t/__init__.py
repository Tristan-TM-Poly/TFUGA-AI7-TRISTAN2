"""Ω-COMPUTE-PHYSICS-T∞ / Ω-COMPLEXITY-ATLAS-T∞.

Empirical, OAK-safe resource modelling for functions and pipelines.

Important epistemic rule: fitted finite-domain scaling is empirical evidence, not a
mathematical proof of asymptotic Big-O/Theta complexity.
"""

from .atlas import ComplexityAtlas, EmpiricalResourceModel, ResourceSample
from .profiler import ProfileResult, profile_call, profile_pipeline

__all__ = [
    "ComplexityAtlas",
    "EmpiricalResourceModel",
    "ResourceSample",
    "ProfileResult",
    "profile_call",
    "profile_pipeline",
]

__version__ = "0.1.0"
