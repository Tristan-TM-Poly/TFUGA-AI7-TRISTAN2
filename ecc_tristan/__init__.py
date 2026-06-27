"""Ω-ECC-T / Error Correction Codes de Tristan.

Executable MVP: Hamming(7,4), binary channels, HyperParityGraph-T,
OAK gating, M⁻ failure memory hooks, small LDPC/OAKBench scaffolds,
soft-decision min-sum decoding, GF(2) linear codes, and interleaving.
"""

from .hamming import DecodeResult, decode, encode, syndrome
from .hyper_parity_graph import HyperParityGraph
from .interleaver import block_deinterleave, block_interleave, block_interleaver_permutation
from .ldpc import LDPCDecodeResult, SparseLDPC
from .linear_block_code import LinearBlockCode, MLDecodeResult
from .minsum import SoftLDPCDecodeResult, hard_bits_from_llr, min_sum_decode
from .benchmarks import BenchmarkResult, bench_hamming74_bsc
from .oakbench_matrix import MatrixRow, default_oakbench_matrix

__all__ = [
    "BenchmarkResult",
    "DecodeResult",
    "HyperParityGraph",
    "LDPCDecodeResult",
    "LinearBlockCode",
    "MLDecodeResult",
    "MatrixRow",
    "SoftLDPCDecodeResult",
    "SparseLDPC",
    "bench_hamming74_bsc",
    "block_deinterleave",
    "block_interleave",
    "block_interleaver_permutation",
    "decode",
    "default_oakbench_matrix",
    "encode",
    "hard_bits_from_llr",
    "min_sum_decode",
    "syndrome",
]
