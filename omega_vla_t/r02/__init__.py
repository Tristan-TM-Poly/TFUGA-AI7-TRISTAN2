"""Ω-VLA-T∞² R0.2-MAX.

A deterministic, checkpointable research-frontier compiler for vector calculus,
linear algebra, operator science and related applications.

The package exposes a very large *logical* address space while materializing
only finite, explicitly budgeted campaigns. Generated research cells are
candidates, not proofs or scientific validation.
"""

from .address import FrontierAddress, FrontierCodec
from .catalogs import CATALOG, Catalog
from .frontier import CampaignConfig, CampaignReport, FrontierController, run_campaign
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
from .theorem_factory import TheoremFactory

__all__ = [
    "CATALOG",
    "CampaignConfig",
    "CampaignReport",
    "Catalog",
    "EpistemicStatus",
    "FrontierAddress",
    "FrontierCodec",
    "FrontierController",
    "MaxOAKReport",
    "ObjectGenome",
    "OperatorGenome",
    "ProblemCell",
    "ResearchArtifact",
    "ResidualProfile",
    "SaturationEntry",
    "SpectralDNA",
    "TheoremFactory",
    "analyze_residual",
    "audit_max_system",
    "run_campaign",
    "spectral_dna",
]

__version__ = "0.2.0"
