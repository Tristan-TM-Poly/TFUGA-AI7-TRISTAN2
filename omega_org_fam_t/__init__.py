"""Ω-ORG-FAM-T: OAK-safe organic molecular-family research infrastructure."""
from .atlas import audit_atlas, compile_atlas
from .classifier import classify_features
from .evidence_engine import EvidenceEngine
from .evidence_models import EvidenceBundle, Peak, SourceRef, SpectralObservation
from .family_space import base_coordinates, evidence_templates, family_cells, iter_requested_cells
from .formula import Species, balance_reaction, is_balanced, parse_formula
from .mixture import MixtureFit, fit_nonnegative_mixture
from .models import ClassificationResult, EvidenceTemplate, FamilyCell, FamilyCoordinate
from .pattern_registry import PatternRegistry, PatternRule, TransformationRule

__all__ = [
    "ClassificationResult",
    "EvidenceBundle",
    "EvidenceEngine",
    "EvidenceTemplate",
    "FamilyCell",
    "FamilyCoordinate",
    "MixtureFit",
    "PatternRegistry",
    "PatternRule",
    "Peak",
    "SourceRef",
    "Species",
    "SpectralObservation",
    "TransformationRule",
    "audit_atlas",
    "balance_reaction",
    "base_coordinates",
    "classify_features",
    "compile_atlas",
    "evidence_templates",
    "family_cells",
    "fit_nonnegative_mixture",
    "is_balanced",
    "iter_requested_cells",
    "parse_formula",
]

__version__ = "0.3.0"
