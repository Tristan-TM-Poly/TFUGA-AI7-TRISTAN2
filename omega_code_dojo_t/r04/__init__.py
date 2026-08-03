"""Ω-CODE-DOJO-T∞ R0.4 synthetic problem-resolution factory."""

from .analyzer import ResolutionAnalyzer
from .benchmark import run_r04_benchmark
from .engine import ResolutionEngine
from .families import FAMILIES, family_catalog
from .models import ResolutionPolicy, ResolutionReceipt
from .portfolio import DEFAULT_PORTFOLIO, ProblemPortfolio

__all__ = [
    "DEFAULT_PORTFOLIO",
    "FAMILIES",
    "ProblemPortfolio",
    "ResolutionAnalyzer",
    "ResolutionEngine",
    "ResolutionPolicy",
    "ResolutionReceipt",
    "family_catalog",
    "run_r04_benchmark",
]
