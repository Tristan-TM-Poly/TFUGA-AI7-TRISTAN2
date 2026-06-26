"""Ω-AUTO²-Kernel v0.5.

Prototype OAK-safe d'automatisation de l'automatisation pour Tristan.
"""

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

__all__ = [
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
]
