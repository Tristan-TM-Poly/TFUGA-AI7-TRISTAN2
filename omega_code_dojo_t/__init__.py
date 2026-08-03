"""Ω-CODE-DOJO-T — OAK-safe local algorithmic training fixtures."""

from .benchmark import MUTANT_SOLVERS, run_oak_benchmark
from .catalog import REFERENCE_SOLVERS, original_catalog
from .codewars import fetch_completed_page, fetch_profile, normalize_progress
from .evaluator import evaluate
from .mminus import MMinusLedger
from .models import FailureRecord, KataTask, SubmissionReport, TaskCase

__all__ = [
    "FailureRecord",
    "KataTask",
    "MMinusLedger",
    "MUTANT_SOLVERS",
    "REFERENCE_SOLVERS",
    "SubmissionReport",
    "TaskCase",
    "evaluate",
    "fetch_completed_page",
    "fetch_profile",
    "normalize_progress",
    "original_catalog",
    "run_oak_benchmark",
]
