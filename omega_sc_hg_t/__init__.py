"""Ω-SC-HG-T∞: OAK-safe bond-orbital-phonon superconductivity search primitives."""

from .evidence import LiteratureClaim, borophene_2026_seed
from .model import BondChannel, OrbitalChannel, PhononChannel, SuperconductingCandidate
from .oak import OAKAssessment, TcEnvelope, audit_candidate, tc_uncertainty_envelope
from .search import adaptive_filter, compare_counterfactuals, pareto_front, rank_candidates

__all__ = [
    "BondChannel",
    "OrbitalChannel",
    "PhononChannel",
    "SuperconductingCandidate",
    "LiteratureClaim",
    "OAKAssessment",
    "TcEnvelope",
    "adaptive_filter",
    "audit_candidate",
    "borophene_2026_seed",
    "compare_counterfactuals",
    "pareto_front",
    "rank_candidates",
    "tc_uncertainty_envelope",
]
