"""Ω-POLYGLOT-BENCH-T R0.3 zero-copy throughput laboratory."""

from .benchmark import benchmark_throughput
from .buffers import NativeAffineLibrary, PreparedAffineCall, as_double_array

__all__ = [
    "benchmark_throughput",
    "NativeAffineLibrary",
    "PreparedAffineCall",
    "as_double_array",
]
__version__ = "0.3.0"
