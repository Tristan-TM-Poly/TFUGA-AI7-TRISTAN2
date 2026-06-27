"""Sparse LDPC-style parity graph and hard-decision decoder for Ω-ECC-T.

This module is intentionally dependency-free. It is not a production LDPC stack;
it is an OAK-safe executable scaffold for experiments before adding optimized
belief propagation / min-sum implementations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Set

from .hyper_parity_graph import hamming_distance


def _binary_rows(rows: Sequence[Sequence[int]]) -> List[List[int]]:
    matrix = [[int(x) for x in row] for row in rows]
    if not matrix:
        raise ValueError("parity matrix must not be empty")
    n = len(matrix[0])
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("parity rows must have a shared non-zero width")
    if any(x not in (0, 1) for row in matrix for x in row):
        raise ValueError("parity matrix must be binary")
    return matrix


def _binary_vector(bits: Sequence[int], n: int) -> List[int]:
    out = [int(x) for x in bits]
    if len(out) != n:
        raise ValueError(f"expected {n} bits")
    if any(x not in (0, 1) for x in out):
        raise ValueError("bits must be binary")
    return out


@dataclass(frozen=True)
class LDPCDecodeResult:
    decoded: List[int]
    syndrome: List[int]
    iterations: int
    flips: int
    converged: bool
    status: str


class SparseLDPC:
    """Sparse binary parity-check code with Gallager-style bit-flip decoding."""

    def __init__(self, parity_checks: Sequence[Sequence[int]], name: str = "SparseLDPC-T") -> None:
        self.parity_checks = _binary_rows(parity_checks)
        self.name = name
        self.m = len(self.parity_checks)
        self.n = len(self.parity_checks[0])
        self.check_to_bits: List[List[int]] = [
            [idx for idx, value in enumerate(row) if value] for row in self.parity_checks
        ]
        if any(len(row) == 0 for row in self.check_to_bits):
            raise ValueError("empty parity checks do not constrain the code")
        self.bit_to_checks: Dict[int, List[int]] = {idx: [] for idx in range(self.n)}
        for check_idx, bits in enumerate(self.check_to_bits):
            for bit_idx in bits:
                self.bit_to_checks[bit_idx].append(check_idx)
        if any(not checks for checks in self.bit_to_checks.values()):
            raise ValueError("every bit must participate in at least one check")

    def syndrome(self, bits: Sequence[int]) -> List[int]:
        vector = _binary_vector(bits, self.n)
        out: List[int] = []
        for row_bits in self.check_to_bits:
            acc = 0
            for idx in row_bits:
                acc ^= vector[idx]
            out.append(acc)
        return out

    def is_codeword(self, bits: Sequence[int]) -> bool:
        return not any(self.syndrome(bits))

    def unsatisfied_checks_by_bit(self, bits: Sequence[int]) -> Dict[int, int]:
        syn = self.syndrome(bits)
        return {
            bit_idx: sum(syn[check_idx] for check_idx in checks)
            for bit_idx, checks in self.bit_to_checks.items()
        }

    def bit_flip_decode(self, received: Sequence[int], max_iterations: int = 20) -> LDPCDecodeResult:
        """Hard-decision iterative decoder.

        At each iteration, flip bits involved in a strict majority of unsatisfied
        checks. If that stalls, flip the uniquely worst bit. This keeps the
        prototype simple while making failures explicit.
        """
        current = _binary_vector(received, self.n)
        total_flips = 0
        for iteration in range(max_iterations + 1):
            syn = self.syndrome(current)
            if not any(syn):
                return LDPCDecodeResult(current, syn, iteration, total_flips, True, "converged")
            if iteration == max_iterations:
                break
            unsatisfied = self.unsatisfied_checks_by_bit(current)
            to_flip: Set[int] = set()
            for bit_idx, count in unsatisfied.items():
                degree = len(self.bit_to_checks[bit_idx])
                if count > degree / 2:
                    to_flip.add(bit_idx)
            if not to_flip:
                best_count = max(unsatisfied.values())
                best_bits = [idx for idx, count in unsatisfied.items() if count == best_count]
                if len(best_bits) == 1 and best_count > 0:
                    to_flip.add(best_bits[0])
                else:
                    return LDPCDecodeResult(current, syn, iteration, total_flips, False, "stalled_oak_uncertain")
            for bit_idx in sorted(to_flip):
                current[bit_idx] ^= 1
            total_flips += len(to_flip)
        final_syndrome = self.syndrome(current)
        return LDPCDecodeResult(current, final_syndrome, max_iterations, total_flips, False, "max_iterations_residual")

    @classmethod
    def toy_6_3(cls) -> "SparseLDPC":
        """Return a tiny [6,~3] sparse parity-check scaffold.

        Checks:
        b0+b1+b3 = 0
        b1+b2+b4 = 0
        b0+b2+b5 = 0
        """
        return cls(
            [
                [1, 1, 0, 1, 0, 0],
                [0, 1, 1, 0, 1, 0],
                [1, 0, 1, 0, 0, 1],
            ],
            name="toy_6_3_ldpc",
        )


def codeword_distance(code: SparseLDPC, a: Sequence[int], b: Sequence[int]) -> int:
    return hamming_distance(_binary_vector(a, code.n), _binary_vector(b, code.n))
