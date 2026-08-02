"""Ω-CONVERGENCE-OS — deterministic, OAK-safe merge analysis."""

from .analyzer import (
    analyze_python_api,
    analyze_script_conflicts,
    analyze_status_conflicts,
    analyze_workflow_permissions,
    build_branch_dna,
    compare_branch_dna,
)
from .models import (
    BranchDNA,
    Conflict,
    ConflictKind,
    FileChange,
    MergePlan,
    MergeReceipt,
    Severity,
)
from .planner import build_merge_plan
from .receipt import build_merge_receipt

__all__ = [
    "BranchDNA",
    "Conflict",
    "ConflictKind",
    "FileChange",
    "MergePlan",
    "MergeReceipt",
    "Severity",
    "analyze_python_api",
    "analyze_script_conflicts",
    "analyze_status_conflicts",
    "analyze_workflow_permissions",
    "build_branch_dna",
    "build_merge_plan",
    "build_merge_receipt",
    "compare_branch_dna",
]

__version__ = "0.1.0"
