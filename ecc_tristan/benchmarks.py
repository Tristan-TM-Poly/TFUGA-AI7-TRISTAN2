"""Tiny deterministic OAKBench for Ω-ECC-T."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

from .channels import binary_symmetric_channel
from .hamming import decode, encode
from .oak import gate_hamming74


@dataclass(frozen=True)
class BenchmarkResult:
    trials: int
    channel: str
    bit_flip_probability: float
    block_success_rate: float
    oak_accept_rate: float
    false_accept_rate: float

    def as_dict(self) -> Dict[str, float | int | str]:
        return asdict(self)


def bench_hamming74_bsc(trials: int = 64, p: float = 0.05, seed: int = 7) -> BenchmarkResult:
    """Benchmark Hamming(7,4) on a BSC.

    False accept means OAK accepted but decoded data differs from source data.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    successes = 0
    oak_accepts = 0
    false_accepts = 0
    for i in range(trials):
        data = [(i >> shift) & 1 for shift in range(4)]
        encoded = encode(data)
        report = binary_symmetric_channel(encoded, p=p, seed=seed + i)
        decoded = decode(report.output_bits)
        oak = gate_hamming74(decoded.syndrome, decoded.corrected_position, decoded.oak_trust)
        if oak.accepted:
            oak_accepts += 1
            if decoded.data_bits != data:
                false_accepts += 1
        if decoded.data_bits == data:
            successes += 1
    return BenchmarkResult(
        trials=trials,
        channel="BSC",
        bit_flip_probability=p,
        block_success_rate=successes / trials,
        oak_accept_rate=oak_accepts / trials,
        false_accept_rate=false_accepts / max(1, oak_accepts),
    )
