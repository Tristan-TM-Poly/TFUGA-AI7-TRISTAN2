"""Ω-ECC-T / Error Correction Codes de Tristan.

Executable MVP: Hamming(7,4), binary channels, HyperParityGraph-T,
OAK gating, M⁻ failure memory hooks, small LDPC/OAKBench scaffolds, and
soft-decision min-sum decoding.
"""

from .hamming import DecodeResult, decode, encode, syndrome
from .hyper_parity_graph import HyperParityGraph
from .ldpc import LDPCDecodeResult, SparseLDPC
from .minsum import SoftLDPCDecodeResult, hard_bits_from_llr, min_sum_decode
from .benchmarks import BenchmarkResult, bench_hamming74_bsc
from .oakbench_matrix import MatrixRow, default_oakbench_matrix

__all__ = [
    "BenchmarkResult",
    "DecodeResult",
    "HyperParityGraph",
    "LDPCDecodeResult",
    "MatrixRow",
    "SoftLDPCDecodeResult",
    "SparseLDPC",
    "bench_hamming74_bsc",
    "decode",
    "default_oakbench_matrix",
    "encode",
    "hard_bits_from_llr",
    "min_sum_decode",
    "syndrome",
]
