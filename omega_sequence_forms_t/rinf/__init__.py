"""Ω-SUITE-FORM-T∞ R∞ scalable discovery architecture.

R∞ exposes a 34,359,738,368-cell logical research space, deterministic
256-family/512-transformation/1,024-antipattern catalogs, exact discovery
petals and OAK-safe campaign tooling. Finite materialization is resource
bounded; the research program has no permanent total cell cap.
"""
from __future__ import annotations

from . import catalog as _catalog

_EXPERIMENTAL_TRANSFORMATION_BACKLOG = frozenset(
    {"normalize_scale", "unit_check", "noether_residue"}
)
_catalog.TRANSFORMATION_SEEDS = tuple(
    seed
    for seed in _catalog.TRANSFORMATION_SEEDS
    if seed.slug not in _EXPERIMENTAL_TRANSFORMATION_BACKLOG
)
if len(_catalog.TRANSFORMATION_SEEDS) != 64:  # pragma: no cover
    raise RuntimeError(
        "canonical R∞ transformation selection must contain exactly 64 seeds; "
        f"found {len(_catalog.TRANSFORMATION_SEEDS)}"
    )

from .active import CandidatePredictor, IndexDiscrimination, rank_discriminating_indices
from .address import CellSpace, FeistelPermutation, TraversalSlice, iter_addresses, sample_addresses
from .benchmark import run_benchmark
from .campaign import CellEstimate, run_campaign
from .catalog import (
    assert_catalog_invariants,
    build_antipattern_catalog,
    build_family_catalog,
    build_transformation_catalog,
    catalog_payload,
)
from .graph import (
    EdgeKind,
    NodeKind,
    RepresentationEdge,
    RepresentationHypergraph,
    RepresentationNode,
)
from .hankel import (
    HankelRankProfile,
    RationalPronyCandidate,
    RationalSpectralTerm,
    discover_rational_prony,
    hankel_rank_profile,
)
from .hypergeometric import HypergeometricCandidate, discover_hypergeometric
from .materialize import materialize_catalog, materialize_cells
from .mminus import FailureObservation, NegativeMemoryRegistry
from .models import (
    AnalyticFamily,
    AntiPatternSpec,
    CampaignBudget,
    CampaignReceipt,
    CellAddress,
    EvidenceArtifact,
    EvidenceLevel,
    FamilyClass,
    FormCandidateRInf,
    Maturity,
    TransformationClass,
    TransformationSpec,
)
from .oak import EvidenceGraph, PromotionDecision, evaluate_promotion
from .orchestrator import DiscoveryLimits, RInfDiscoveryReport, discover_rinf
from .p_recursive import PRecursiveCandidate, PRecursiveOperator, discover_p_recursive
from .quasipolynomial import QuasiPolynomialCandidate, discover_quasi_polynomials
from .rational_index import RationalIndexCandidate, discover_rational_indices
from .residual import (
    ResidualCandidate,
    ResidualDecomposition,
    ResidualLayer,
    greedy_residual_decompose,
)

__all__ = [
    "AnalyticFamily",
    "AntiPatternSpec",
    "CampaignBudget",
    "CampaignReceipt",
    "CandidatePredictor",
    "CellAddress",
    "CellEstimate",
    "CellSpace",
    "DiscoveryLimits",
    "EdgeKind",
    "EvidenceArtifact",
    "EvidenceGraph",
    "EvidenceLevel",
    "FailureObservation",
    "FamilyClass",
    "FeistelPermutation",
    "FormCandidateRInf",
    "HankelRankProfile",
    "HypergeometricCandidate",
    "IndexDiscrimination",
    "Maturity",
    "NegativeMemoryRegistry",
    "NodeKind",
    "PRecursiveCandidate",
    "PRecursiveOperator",
    "PromotionDecision",
    "QuasiPolynomialCandidate",
    "RInfDiscoveryReport",
    "RationalIndexCandidate",
    "RationalPronyCandidate",
    "RationalSpectralTerm",
    "RepresentationEdge",
    "RepresentationHypergraph",
    "RepresentationNode",
    "ResidualCandidate",
    "ResidualDecomposition",
    "ResidualLayer",
    "TransformationClass",
    "TransformationSpec",
    "TraversalSlice",
    "assert_catalog_invariants",
    "build_antipattern_catalog",
    "build_family_catalog",
    "build_transformation_catalog",
    "catalog_payload",
    "discover_hypergeometric",
    "discover_p_recursive",
    "discover_quasi_polynomials",
    "discover_rational_indices",
    "discover_rational_prony",
    "discover_rinf",
    "evaluate_promotion",
    "greedy_residual_decompose",
    "hankel_rank_profile",
    "iter_addresses",
    "materialize_catalog",
    "materialize_cells",
    "rank_discriminating_indices",
    "run_benchmark",
    "run_campaign",
    "sample_addresses",
]

__version__ = "0.∞.0"
