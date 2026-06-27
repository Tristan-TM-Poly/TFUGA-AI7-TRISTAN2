"""OAK gates for accepting or rejecting ECC reconstructions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple


@dataclass(frozen=True)
class OAKDecision:
    accepted: bool
    status: str
    residual_syndrome_weight: int
    correction_weight: int
    trust: float
    reason: str


def hamming_weight(bits: Sequence[int]) -> int:
    return sum(1 for b in bits if int(b) != 0)


def gate_hamming74(
    syndrome: Tuple[int, int, int],
    corrected_position: int,
    trust: float,
    max_corrected_bits: int = 1,
    min_trust: float = 0.5,
) -> OAKDecision:
    """Accept only clean or single-bit-candidate Hamming corrections."""
    residual = hamming_weight(syndrome)
    correction_weight = 1 if corrected_position else 0
    if correction_weight > max_corrected_bits:
        return OAKDecision(False, "reject", residual, correction_weight, trust, "too_many_corrected_bits")
    if trust < min_trust:
        return OAKDecision(False, "reject", residual, correction_weight, trust, "trust_below_threshold")
    if corrected_position < 0 or corrected_position > 7:
        return OAKDecision(False, "reject", residual, correction_weight, trust, "invalid_correction_position")
    return OAKDecision(True, "accept", residual, correction_weight, trust, "within_hamming74_oak_limits")
