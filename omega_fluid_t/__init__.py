"""Ω-FLUID-T∞²: OAK-safe fluid-model research kernel."""

from .dimensionless import DimensionlessInput, DimensionlessNumbers, compute_dimensionless
from .frontier import FluidFrontierSpace, FrontierWriter, default_fluid_space
from .genome import FluidGenome
from .oak import OAKBenchmarkReport, run_core_benchmarks

__all__ = [
    "DimensionlessInput",
    "DimensionlessNumbers",
    "FluidFrontierSpace",
    "FluidGenome",
    "FrontierWriter",
    "OAKBenchmarkReport",
    "compute_dimensionless",
    "default_fluid_space",
    "run_core_benchmarks",
]

__version__ = "0.1.0"
