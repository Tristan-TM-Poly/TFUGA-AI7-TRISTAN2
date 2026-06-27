"""HyperParityGraph-T: small binary parity graph prototype.

This is intentionally minimal: it supports binary parity constraints, syndrome
calculation, and exhaustive nearest-codeword decoding for small n. It is a
baseline for later LDPC / belief propagation / CVCD expansions.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import List, Sequence


def _validate_matrix(matrix: Sequence[Sequence[int]]) -> List[List[int]]:
    rows = [[int(x) for x in row] for row in matrix]
    if not rows:
        raise ValueError("matrix must have at least one row")
    width = len(rows[0])
    if width == 0:
        raise ValueError("matrix must have at least one column")
    if any(len(row) != width for row in rows):
        raise ValueError("all parity rows must have the same length")
    if any(x not in (0, 1) for row in rows for x in row):
        raise ValueError("matrix must be binary")
    return rows


def _validate_vector(vector: Sequence[int], n: int) -> List[int]:
    out = [int(x) for x in vector]
    if len(out) != n:
        raise ValueError(f"expected vector of length {n}")
    if any(x not in (0, 1) for x in out):
        raise ValueError("vector must be binary")
    return out


def xor_dot(row: Sequence[int], vector: Sequence[int]) -> int:
    acc = 0
    for a, b in zip(row, vector):
        if a:
            acc ^= int(b)
    return acc


def hamming_distance(a: Sequence[int], b: Sequence[int]) -> int:
    return sum(int(x) != int(y) for x, y in zip(a, b))


@dataclass(frozen=True)
class HyperParityDecodeResult:
    codeword: List[int]
    syndrome: List[int]
    distance: int
    candidates_checked: int
    status: str


class HyperParityGraph:
    """Binary parity-check hypergraph over GF(2)."""

    def __init__(self, parity_checks: Sequence[Sequence[int]], name: str = "HyperParityGraph-T") -> None:
        self.parity_checks = _validate_matrix(parity_checks)
        self.name = name
        self.n = len(self.parity_checks[0])
        self.m = len(self.parity_checks)

    def syndrome(self, vector: Sequence[int]) -> List[int]:
        v = _validate_vector(vector, self.n)
        return [xor_dot(row, v) for row in self.parity_checks]

    def is_codeword(self, vector: Sequence[int]) -> bool:
        return all(bit == 0 for bit in self.syndrome(vector))

    def enumerate_codewords(self, max_n: int = 16) -> List[List[int]]:
        if self.n > max_n:
            raise ValueError("exhaustive enumeration is limited; use a real LDPC decoder for large n")
        return [list(bits) for bits in product((0, 1), repeat=self.n) if self.is_codeword(bits)]

    def nearest_codeword(self, received: Sequence[int], max_n: int = 16) -> HyperParityDecodeResult:
        r = _validate_vector(received, self.n)
        syn = self.syndrome(r)
        if all(x == 0 for x in syn):
            return HyperParityDecodeResult(r, syn, 0, 1, "already_codeword")
        codewords = self.enumerate_codewords(max_n=max_n)
        best = min(codewords, key=lambda c: hamming_distance(c, r))
        dist = hamming_distance(best, r)
        ties = sum(1 for c in codewords if hamming_distance(c, r) == dist)
        status = "nearest_unique" if ties == 1 else "nearest_tie_oak_uncertain"
        return HyperParityDecodeResult(best, syn, dist, len(codewords), status)

    @classmethod
    def repetition3(cls) -> "HyperParityGraph":
        # Constraints: b0=b1 and b1=b2.
        return cls([[1, 1, 0], [0, 1, 1]], name="repetition3")
