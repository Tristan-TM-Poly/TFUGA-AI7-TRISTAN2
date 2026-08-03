"""Ω-WEB-HG-T∞ R0.2 incremental evidence crawler."""

from .audit import audit_run
from .diffing import compare_run_directories
from .engine import IncrementalWebHypergraphCrawler
from .models import R02Config, RunBundle
from .state import StateStore

__all__ = [
    "IncrementalWebHypergraphCrawler",
    "R02Config",
    "RunBundle",
    "StateStore",
    "audit_run",
    "compare_run_directories",
]
