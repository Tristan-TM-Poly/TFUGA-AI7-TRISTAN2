"""Minimal executable utilities for the TFUGA / SAGE-TRISTAN canon."""

from .algebra_defect_lab import FiniteDimensionalAlgebra
from .hgfm_core import HGFMGraph, HGFMHyperEdge, HGFMNode, HGFMNodeState
from .negative_memory import NegativeMemoryBank, NegativeMemoryEntry
from .omega_math_tristan import (
    BayesTristanVector,
    ClaimCard,
    OAK_LEVELS,
    action_score,
    classify_oak_status,
    canonicalization_score,
    next_action_hint,
)
from .prime_tensors import first_primes, gap_sequence, residue_signature

__all__ = [
    "BayesTristanVector",
    "ClaimCard",
    "FiniteDimensionalAlgebra",
    "HGFMGraph",
    "HGFMHyperEdge",
    "HGFMNode",
    "HGFMNodeState",
    "NegativeMemoryBank",
    "NegativeMemoryEntry",
    "OAK_LEVELS",
    "action_score",
    "classify_oak_status",
    "canonicalization_score",
    "first_primes",
    "gap_sequence",
    "next_action_hint",
    "residue_signature",
]
