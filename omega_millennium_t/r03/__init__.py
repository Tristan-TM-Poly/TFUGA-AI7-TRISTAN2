"""Ω-PROBLEM-ATLAS-T∞ R0.3.

Deterministic, OAK-safe infrastructure for organizing open-problem catalogs,
competition streams, research targets, evidence cells and transferable methods.
No open-problem solution or current-status certification is claimed.
"""

from .atlas import (
    ATTACK_MODES,
    FRONTS,
    ProblemRecord,
    ResearchCell,
    SourceSpec,
    audit_output,
    build_seed_records,
    compile_atlas,
    expand_research_cells,
    load_source_registry,
    select_portfolio,
)
from .max_engine import (
    METHOD_FAMILIES,
    TARGET_KINDS,
    MaxResearchCell,
    ResearchTarget,
    audit_max_output,
    compile_max_atlas,
    deduplicate_records_max,
    expand_max_cells,
    expand_research_targets,
    select_balanced_portfolio,
    unicode_canonical_key,
)
from .strict_audit import audit_max_output_strict

__all__ = [
    "ATTACK_MODES",
    "FRONTS",
    "METHOD_FAMILIES",
    "TARGET_KINDS",
    "MaxResearchCell",
    "ProblemRecord",
    "ResearchCell",
    "ResearchTarget",
    "SourceSpec",
    "audit_max_output",
    "audit_max_output_strict",
    "audit_output",
    "build_seed_records",
    "compile_atlas",
    "compile_max_atlas",
    "deduplicate_records_max",
    "expand_max_cells",
    "expand_research_cells",
    "expand_research_targets",
    "load_source_registry",
    "select_balanced_portfolio",
    "select_portfolio",
    "unicode_canonical_key",
]

__version__ = "0.3.2"
