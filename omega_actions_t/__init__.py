"""Ω-ACTIONS-T∞: OAK-safe GitHub Actions optimization tooling."""

from .analyzer import analyze_repository, analyze_workflow, render_markdown, write_report
from .auto_optimizer import compile_candidate, propose_actions
from .cache_tensor import analyze_caches
from .compiler import compile_workflow, validate_ir
from .delta_ci import plan_delta, write_delta_report
from .digital_twin import simulate_workflow
from .evidence import build_evidence_bundle, write_bundle
from .project_surface import validate_project_scripts
from .promotion import compare_telemetry
from .sharding import shard_tests
from .telemetry import analyze_telemetry, write_telemetry_report
from .trigger_hotspots import analyze_trigger_hotspots, extract_positive_paths

__all__ = [
    "analyze_repository",
    "analyze_workflow",
    "render_markdown",
    "write_report",
    "compile_candidate",
    "propose_actions",
    "analyze_caches",
    "compile_workflow",
    "validate_ir",
    "plan_delta",
    "write_delta_report",
    "simulate_workflow",
    "build_evidence_bundle",
    "write_bundle",
    "validate_project_scripts",
    "compare_telemetry",
    "shard_tests",
    "analyze_telemetry",
    "write_telemetry_report",
    "analyze_trigger_hotspots",
    "extract_positive_paths",
]
