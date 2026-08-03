"""Ω-CODE-DOJO-T∞ R0.2 — extensible OAK-safe algorithmic research factory."""

from .benchmark import run_r02_benchmark
from .campaign import CampaignEngine
from .frontier import DEFAULT_FRONTIER, LogicalFrontier
from .models import CampaignPolicy, FrontierCell, TaskIR
from .task_ir import TaskIRCompiler

__all__ = [
    "CampaignEngine",
    "CampaignPolicy",
    "DEFAULT_FRONTIER",
    "FrontierCell",
    "LogicalFrontier",
    "TaskIR",
    "TaskIRCompiler",
    "run_r02_benchmark",
]
