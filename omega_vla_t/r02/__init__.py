"""Ω-VLA-T∞² R0.2-MAX.

A deterministic, checkpointable research-frontier compiler for vector calculus,
linear algebra, operator science and related applications.

The package exposes a very large *logical* address space while materializing
only finite, explicitly budgeted campaigns. Generated research cells are
candidates, not proofs or scientific validation.
"""

from .address import FrontierAddress, FrontierCodec
from .catalogs import CATALOG, Catalog
from .discrete_exterior import (
    ChainComplexAudit,
    DiscreteHodgeReport,
    FiniteChainComplex,
    filled_oriented_triangle,
    oriented_cycle_incidence,
)
from .formal_targets import FormalTarget, LeanTargetCompiler
from .frontier import CampaignConfig, CampaignReport, FrontierController, run_campaign
from .linearization_atlas import (
    AtlasTransition,
    LinearizationAtlas,
    LinearizationCell,
    build_linearization_atlas,
    build_linearization_cell,
)
from .models import (
    EpistemicStatus,
    ObjectGenome,
    OperatorGenome,
    ProblemCell,
    ResearchArtifact,
    SaturationEntry,
)
from .oak_max import MaxOAKReport, audit_max_system
from .residual_intelligence import ResidualProfile, analyze_residual
from .spectral_dna import SpectralDNA, spectral_dna
from .sqlite_index import SQLiteDigestIndex
from .store import StreamingShardedJSONLWriter
from .theorem_factory import TheoremFactory

__all__ = [
    "AtlasTransition",
    "CATALOG",
    "CampaignConfig",
    "CampaignReport",
    "Catalog",
    "ChainComplexAudit",
    "DiscreteHodgeReport",
    "EpistemicStatus",
    "FiniteChainComplex",
    "FormalTarget",
    "FrontierAddress",
    "FrontierCodec",
    "FrontierController",
    "LeanTargetCompiler",
    "LinearizationAtlas",
    "LinearizationCell",
    "MaxOAKReport",
    "ObjectGenome",
    "OperatorGenome",
    "ProblemCell",
    "ResearchArtifact",
    "ResidualProfile",
    "SQLiteDigestIndex",
    "SaturationEntry",
    "SpectralDNA",
    "StreamingShardedJSONLWriter",
    "TheoremFactory",
    "analyze_residual",
    "audit_max_system",
    "build_linearization_atlas",
    "build_linearization_cell",
    "filled_oriented_triangle",
    "oriented_cycle_incidence",
    "run_campaign",
    "spectral_dna",
]

__version__ = "0.2.0"
