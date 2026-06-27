"""Soft-decision min-sum decoder for sparse LDPC-style parity graphs.

This is the first executable BayesDecoder_T-adjacent layer: channel evidence is
represented as log-likelihood ratios (LLRs), parity checks pass messages, and
OAK receives an explicit convergence / residual status.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .ldpc import SparseLDPC


@dataclass(frozen=True)
class SoftLDPCDecodeResult:
    decoded: List[int]
    posterior_llr: List[float]
    syndrome: List[int]
    iterations: int
    converged: bool
    status: str
    min_abs_posterior_llr: float

    @property
    def weak_positions(self) -> List[int]:
        """Return bit positions whose posterior reliability is near the weakest."""
        if not self.posterior_llr:
            return []
        floor = max(self.min_abs_posterior_llr, 1e-12)
        return [idx for idx, value in enumerate(self.posterior_llr) if abs(value) <= 2.0 * floor]


def hard_bits_from_llr(llr: Sequence[float]) -> List[int]:
    """Map positive/zero LLR to bit 0 and negative LLR to bit 1."""
    return [0 if float(value) >= 0.0 else 1 for value in llr]


def _validate_llr(llr: Sequence[float], n: int) -> List[float]:
    out = [float(value) for value in llr]
    if len(out) != n:
        raise ValueError(f"expected {n} LLR values")
    return out


def min_sum_decode(
    code: SparseLDPC,
    llr: Sequence[float],
    max_iterations: int = 20,
    normalize: float = 1.0,
    offset: float = 0.0,
) -> SoftLDPCDecodeResult:
    """Decode a sparse parity-check code from channel LLRs using min-sum.

    Parameters
    ----------
    code:
        Sparse binary parity-check code.
    llr:
        Channel log-likelihood ratios. Positive means bit 0 is more likely;
        negative means bit 1 is more likely.
    max_iterations:
        Maximum message-passing iterations.
    normalize:
        Optional normalized-min-sum scale in ``(0, +∞)``.
    offset:
        Optional offset-min-sum subtraction, clipped at zero.

    OAK-safe note: this transparent implementation is for small research
    scaffolds. It is not a hardware-optimized LDPC decoder.
    """
    if max_iterations < 0:
        raise ValueError("max_iterations must be non-negative")
    if normalize <= 0.0:
        raise ValueError("normalize must be positive")
    if offset < 0.0:
        raise ValueError("offset must be non-negative")

    channel = _validate_llr(llr, code.n)
    check_to_var: Dict[Tuple[int, int], float] = {}
    var_to_check: Dict[Tuple[int, int], float] = {}

    for check_idx, bits in enumerate(code.check_to_bits):
        for bit_idx in bits:
            edge = (check_idx, bit_idx)
            var_to_check[edge] = channel[bit_idx]
            check_to_var[edge] = 0.0

    posterior = list(channel)
    hard = hard_bits_from_llr(posterior)
    syn = code.syndrome(hard)
    if not any(syn):
        min_abs = min((abs(value) for value in posterior), default=0.0)
        return SoftLDPCDecodeResult(hard, posterior, syn, 0, True, "converged_initial", min_abs)

    for iteration in range(1, max_iterations + 1):
        # Check-node update: sign product and minimum magnitude excluding target bit.
        for check_idx, bits in enumerate(code.check_to_bits):
            for bit_idx in bits:
                others = [var_to_check[(check_idx, other)] for other in bits if other != bit_idx]
                if not others:
                    check_to_var[(check_idx, bit_idx)] = 0.0
                    continue
                sign = 1.0
                min_abs = float("inf")
                for message in others:
                    if message < 0.0:
                        sign *= -1.0
                    magnitude = abs(message)
                    if magnitude < min_abs:
                        min_abs = magnitude
                check_to_var[(check_idx, bit_idx)] = sign * max(0.0, min_abs - offset) * normalize

        # A posteriori LLRs and hard decision.
        posterior = []
        for bit_idx in range(code.n):
            total = channel[bit_idx]
            for check_idx in code.bit_to_checks[bit_idx]:
                total += check_to_var[(check_idx, bit_idx)]
            posterior.append(total)

        hard = hard_bits_from_llr(posterior)
        syn = code.syndrome(hard)
        min_abs = min((abs(value) for value in posterior), default=0.0)
        if not any(syn):
            return SoftLDPCDecodeResult(hard, posterior, syn, iteration, True, "converged", min_abs)

        # Variable-node update: extrinsic channel + all other incoming check messages.
        for check_idx, bits in enumerate(code.check_to_bits):
            for bit_idx in bits:
                total = channel[bit_idx]
                for other_check in code.bit_to_checks[bit_idx]:
                    if other_check != check_idx:
                        total += check_to_var[(other_check, bit_idx)]
                var_to_check[(check_idx, bit_idx)] = total

    min_abs = min((abs(value) for value in posterior), default=0.0)
    return SoftLDPCDecodeResult(hard, posterior, syn, max_iterations, False, "max_iterations_residual", min_abs)
