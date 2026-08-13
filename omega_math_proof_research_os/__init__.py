"""Ω-MATH-PROOF-RESEARCH-OS R0.1.

A small, OAK-safe contract layer for turning provenance-preserving
mathematics document harvests into structured research artifacts.
"""

from .contracts import MathArtifact, ProofGenome, SourceAnchor

__all__ = ["MathArtifact", "ProofGenome", "SourceAnchor"]
__version__ = "0.1.0"
