"""Ω Meta Morphogenesis Fixed-Point kernel.

Dependency-free primitives for proof-carrying transformations, residual allocation,
epistemic/authority gates, capability crystallization, and meta-stop decisions.
"""

from .kernel import (
    AuthorityEnvelope,
    CapabilityCrystal,
    EpistemicStatus,
    KernelDecision,
    MorphogenesisKernel,
    ProofCarryingTransformation,
    Residual,
    TransformationMetrics,
)

__all__ = [
    "AuthorityEnvelope",
    "CapabilityCrystal",
    "EpistemicStatus",
    "KernelDecision",
    "MorphogenesisKernel",
    "ProofCarryingTransformation",
    "Residual",
    "TransformationMetrics",
]
