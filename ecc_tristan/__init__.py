"""Ω-ECC-T / Error Correction Codes de Tristan.

Executable MVP: Hamming(7,4), binary channels, HyperParityGraph-T,
OAK gating, and M⁻ failure memory hooks.
"""

from .hamming import DecodeResult, decode, encode, syndrome
from .hyper_parity_graph import HyperParityGraph
from .benchmarks import BenchmarkResult, bench_hamming74_bsc

__all__ = [
    "BenchmarkResult",
    "DecodeResult",
    "HyperParityGraph",
    "bench_hamming74_bsc",
    "decode",
    "encode",
    "syndrome",
]
