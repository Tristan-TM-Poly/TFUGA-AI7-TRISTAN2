"""Ω-ASM-T∞ — OAK-safe assembly optimization and evidence laboratory."""

from .analysis import analyze, cvcd_signature, dependency_graph
from .backends import emit_dot_u64, supported_variants
from .benchmark import BenchmarkStats, machine_manifest, relative_ratio, summarize_samples
from .cost_model import StaticCostProfile, get_static_cost_profile, static_cost_profiles
from .counters import (
    DEFAULT_PERF_EVENTS,
    HARDWARE_PERF_EVENTS,
    PerfCounter,
    PerfParseResult,
    build_p5_report,
    derive_counter_metrics,
    parse_perf_stat_csv,
    requested_perf_events,
)
from .ir import dot_u64_block_program, program_from_dict, validate_program
from .microarch import (
    CacheDescriptor,
    cache_descriptors,
    file_sha256,
    microarchitecture_manifest,
    normalize_architecture,
    parse_size_bytes,
    toolchain_manifest,
)
from .oak import oak_report
from .search import estimate_builtin_candidates, pareto_front

__all__ = [
    "BenchmarkStats",
    "CacheDescriptor",
    "DEFAULT_PERF_EVENTS",
    "HARDWARE_PERF_EVENTS",
    "PerfCounter",
    "PerfParseResult",
    "StaticCostProfile",
    "analyze",
    "build_p5_report",
    "cache_descriptors",
    "cvcd_signature",
    "dependency_graph",
    "derive_counter_metrics",
    "dot_u64_block_program",
    "emit_dot_u64",
    "estimate_builtin_candidates",
    "file_sha256",
    "get_static_cost_profile",
    "machine_manifest",
    "microarchitecture_manifest",
    "normalize_architecture",
    "oak_report",
    "pareto_front",
    "parse_perf_stat_csv",
    "parse_size_bytes",
    "program_from_dict",
    "relative_ratio",
    "requested_perf_events",
    "static_cost_profiles",
    "summarize_samples",
    "supported_variants",
    "toolchain_manifest",
    "validate_program",
]

__version__ = "0.4.0"
