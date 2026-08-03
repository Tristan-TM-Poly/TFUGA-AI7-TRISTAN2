"""Ω-PROBLEM-ATLAS-T∞ R0.3.

Deterministic, OAK-safe infrastructure for organizing open-problem catalogs,
competition streams, research cells and transferable mathematical methods.
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

__all__ = [
    "ATTACK_MODES",
    "FRONTS",
    "ProblemRecord",
    "ResearchCell",
    "SourceSpec",
    "audit_output",
    "build_seed_records",
    "compile_atlas",
    "expand_research_cells",
    "load_source_registry",
    "select_portfolio",
]

__version__ = "0.3.0"
