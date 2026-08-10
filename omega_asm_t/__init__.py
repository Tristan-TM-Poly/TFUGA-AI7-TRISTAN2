"""Ω-ASM-T∞ R1 — OAK-safe assembly optimization laboratory."""

from .analysis import analyze, cvcd_signature, dependency_graph
from .backends import emit_dot_u64, supported_variants
from .benchmark import BenchmarkStats, machine_manifest, relative_ratio, summarize_samples
from .cost_model import StaticCostProfile, get_static_cost_profile, static_cost_profiles
from .ir import dot_u64_block_program, program_from_dict, validate_program
from .oak import oak_report
from .search import estimate_builtin_candidates, pareto_front

__all__ = [
    "BenchmarkStats",
    "StaticCostProfile",
    "analyze",
    "cvcd_signature",
    "dependency_graph",
    "dot_u64_block_program",
    "emit_dot_u64",
    "estimate_builtin_candidates",
    "get_static_cost_profile",
    "machine_manifest",
    "oak_report",
    "pareto_front",
    "program_from_dict",
    "relative_ratio",
    "static_cost_profiles",
    "summarize_samples",
    "supported_variants",
    "validate_program",
]

__version__ = "0.3.0"
