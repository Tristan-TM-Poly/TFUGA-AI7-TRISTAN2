"""Ω-AUTO²-Kernel v0.9.

Prototype OAK-safe d'automatisation de l'automatisation pour Tristan.
"""

__version__ = "0.9.0"

from .models import FrictionTensor, Workflow, OAKReport
from .friction import compute_priority_score
from .workflow_synth import forge_workflow_from_task
from .oak_gate import evaluate_workflow
from .capabilities import CapacityVector, CapabilityAssessment, assess_capability, infer_capacity_vector
from .sandbox import DryRunReport, dry_run_workflow
from .telemetry import TelemetrySnapshot
from .proof import ProofOfWorkflow, prove_workflow
from .improver import improve_draft
from .bench import BenchResult, run_bench, run_suite
from .report import build_markdown_report
from .canonical import CANONICAL_TASKS, canonical_workflow, canonical_workflows
from .exporters import suite_json, suite_markdown
from .score_compare import compare_scores
from .regression import current_canonical_suite, regression_check
from .snapshot import canonical_snapshot, snapshot_json, load_snapshot
from .diff_report import build_diff_payload, diff_json, diff_markdown
from .release import quality_gate, release_pipeline, release_markdown

__all__ = [
    "__version__",
    "FrictionTensor",
    "Workflow",
    "OAKReport",
    "compute_priority_score",
    "forge_workflow_from_task",
    "evaluate_workflow",
    "CapacityVector",
    "CapabilityAssessment",
    "assess_capability",
    "infer_capacity_vector",
    "DryRunReport",
    "dry_run_workflow",
    "TelemetrySnapshot",
    "ProofOfWorkflow",
    "prove_workflow",
    "improve_draft",
    "BenchResult",
    "run_bench",
    "run_suite",
    "build_markdown_report",
    "CANONICAL_TASKS",
    "canonical_workflow",
    "canonical_workflows",
    "suite_json",
    "suite_markdown",
    "compare_scores",
    "current_canonical_suite",
    "regression_check",
    "canonical_snapshot",
    "snapshot_json",
    "load_snapshot",
    "build_diff_payload",
    "diff_json",
    "diff_markdown",
    "quality_gate",
    "release_pipeline",
    "release_markdown",
]
