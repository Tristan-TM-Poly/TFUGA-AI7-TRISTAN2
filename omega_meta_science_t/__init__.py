"""Ω-META-SCIENCE-FOUNDRY-T∞² executable research kernel."""

from .benchmark import build_fixture, run_benchmark, run_strategy
from .models import BenchmarkReport, Experiment, StrategyResult, TheoryGenome
from .oak import FAULT_TYPES, evaluate_oak, meta_oak_mutation_campaign

__all__ = [
    "BenchmarkReport",
    "Experiment",
    "FAULT_TYPES",
    "StrategyResult",
    "TheoryGenome",
    "build_fixture",
    "evaluate_oak",
    "meta_oak_mutation_campaign",
    "run_benchmark",
    "run_strategy",
]

__version__ = "0.1.0"
