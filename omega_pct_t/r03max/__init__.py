"""Ω-PCT∞ R0.3 MAX: typed theory generation and OAK compilation."""

from .campaign import CampaignBudget, CampaignRunner, CampaignState
from .lagrangian_ir import CompiledTheory, LagrangianCompiler, load_theory, parse_theory
from .model_generator import dark_vector_candidate, scalar_portal_candidate, vectorlike_fermion_candidate
from .oakbench import OAKBench, OAKPolicy
from .operators import OperatorGenerationBudget, generate_scalar_monomials
from .pdg_absorber import SnapshotManifest, absorb_snapshot
from .symmetry import LieGroup, SymmetryCompiler, parse_group
from .types import EpistemicStatus, FieldSpec, OperatorSpec, TheorySpec, ValidationReport

__all__ = [
    "CampaignBudget",
    "CampaignRunner",
    "CampaignState",
    "CompiledTheory",
    "LagrangianCompiler",
    "load_theory",
    "parse_theory",
    "dark_vector_candidate",
    "scalar_portal_candidate",
    "vectorlike_fermion_candidate",
    "OAKBench",
    "OAKPolicy",
    "OperatorGenerationBudget",
    "generate_scalar_monomials",
    "SnapshotManifest",
    "absorb_snapshot",
    "LieGroup",
    "SymmetryCompiler",
    "parse_group",
    "EpistemicStatus",
    "FieldSpec",
    "OperatorSpec",
    "TheorySpec",
    "ValidationReport",
]

__version__ = "0.3.0"
