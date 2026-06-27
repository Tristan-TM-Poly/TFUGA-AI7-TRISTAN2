"""GF(2) linear algebra primitives for Ω-ECC-T.

Dependency-free utilities for small auditable code construction, syndrome
analysis, rank/nullspace checks, and exhaustive OAK baselines.
"""
from __future__ import annotations

from itertools import product
from typing import Iterable, List, Sequence, Tuple

BitVector = List[int]
BitMatrix = List[List[int]]


def validate_bits(vector: Sequence[int], width: int | None = None, name: str = "vector") -> BitVector:
    out = [int(x) for x in vector]
    if width is not None and len(out) != width:
        raise ValueError(f"{name} must have length {width}")
    if any(x not in (0, 1) for x in out):
        raise ValueError(f"{name} must be binary")
    return out


def validate_matrix(matrix: Sequence[Sequence[int]], name: str = "matrix") -> BitMatrix:
    rows = [[int(x) for x in row] for row in matrix]
    if not rows:
        raise ValueError(f"{name} must not be empty")
    width = len(rows[0])
    if width == 0:
        raise ValueError(f"{name} must have at least one column")
    if any(len(row) != width for row in rows):
        raise ValueError(f"{name} rows must have equal width")
    if any(x not in (0, 1) for row in rows for x in row):
        raise ValueError(f"{name} must be binary")
    return rows


def dot_mod2(a: Sequence[int], b: Sequence[int]) -> int:
    if len(a) != len(b):
        raise ValueError("vectors must have equal length")
    acc = 0
    for x, y in zip(a, b):
        if int(x) & int(y):
            acc ^= 1
    return acc


def mat_vec_mul_mod2(matrix: Sequence[Sequence[int]], vector: Sequence[int]) -> BitVector:
    rows = validate_matrix(matrix)
    v = validate_bits(vector, len(rows[0]))
    return [dot_mod2(row, v) for row in rows]


def vec_mat_mul_mod2(vector: Sequence[int], matrix: Sequence[Sequence[int]]) -> BitVector:
    rows = validate_matrix(matrix)
    v = validate_bits(vector, len(rows))
    width = len(rows[0])
    out: BitVector = []
    for col in range(width):
        acc = 0
        for row_idx, bit in enumerate(v):
            if bit & rows[row_idx][col]:
                acc ^= 1
        out.append(acc)
    return out


def transpose(matrix: Sequence[Sequence[int]]) -> BitMatrix:
    rows = validate_matrix(matrix)
    return [list(col) for col in zip(*rows)]


def rref_mod2(matrix: Sequence[Sequence[int]]) -> Tuple[BitMatrix, List[int]]:
    rows = validate_matrix(matrix)
    work = [row[:] for row in rows]
    row = 0
    pivots: List[int] = []
    height = len(work)
    width = len(work[0])
    for col in range(width):
        pivot = None
        for candidate in range(row, height):
            if work[candidate][col]:
                pivot = candidate
                break
        if pivot is None:
            continue
        work[row], work[pivot] = work[pivot], work[row]
        for r in range(height):
            if r != row and work[r][col]:
                work[r] = [a ^ b for a, b in zip(work[r], work[row])]
        pivots.append(col)
        row += 1
        if row == height:
            break
    return work, pivots


def rank_mod2(matrix: Sequence[Sequence[int]]) -> int:
    _, pivots = rref_mod2(matrix)
    return len(pivots)


def nullspace_mod2(matrix: Sequence[Sequence[int]]) -> BitMatrix:
    rows = validate_matrix(matrix)
    rref, pivots = rref_mod2(rows)
    width = len(rows[0])
    pivot_set = set(pivots)
    free_cols = [col for col in range(width) if col not in pivot_set]
    basis: BitMatrix = []
    for free_col in free_cols:
        vector = [0] * width
        vector[free_col] = 1
        for pivot_row, pivot_col in enumerate(pivots):
            vector[pivot_col] = rref[pivot_row][free_col]
        basis.append(vector)
    return basis


def hamming_weight(vector: Sequence[int]) -> int:
    return sum(1 for bit in vector if int(bit) != 0)


def hamming_distance(a: Sequence[int], b: Sequence[int]) -> int:
    if len(a) != len(b):
        raise ValueError("vectors must have equal length")
    return sum(int(x) != int(y) for x, y in zip(a, b))


def all_binary_vectors(width: int) -> Iterable[BitVector]:
    if width < 0:
        raise ValueError("width must be non-negative")
    for bits in product((0, 1), repeat=width):
        yield list(bits)
