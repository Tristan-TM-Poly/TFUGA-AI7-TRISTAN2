"""Ω-HYPERPHASE-MAT-T∞ — OAK-safe hypergraph thermodynamics reference package."""

from .atlas import PhaseHypergraphAtlas, PhaseNode, TransitionHyperedge
from .claims import ALLOWED_STATUSES, CLAIMS, Claim
from .examples import four_site_topology_ensemble
from .model import (
    CrossoverMarker,
    ExactHypergraphEnsemble,
    Hyperedge,
    HypergraphState,
    Microstate,
    ThermodynamicState,
    finite_size_crossover,
)

__all__ = [
    "ALLOWED_STATUSES",
    "CLAIMS",
    "Claim",
    "CrossoverMarker",
    "ExactHypergraphEnsemble",
    "Hyperedge",
    "HypergraphState",
    "Microstate",
    "PhaseHypergraphAtlas",
    "PhaseNode",
    "ThermodynamicState",
    "TransitionHyperedge",
    "finite_size_crossover",
    "four_site_topology_ensemble",
]
