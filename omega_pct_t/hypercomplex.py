from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import sqrt
from typing import Iterable, Sequence


def _conjugate(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        return ()
    return (float(values[0]), *(-float(value) for value in values[1:]))


def cayley_dickson_multiply(a: Sequence[float], b: Sequence[float]) -> tuple[float, ...]:
    if len(a) != len(b) or len(a) == 0 or len(a) & (len(a) - 1):
        raise ValueError("Cayley-Dickson vectors must have equal power-of-two lengths")
    if len(a) == 1:
        return (float(a[0]) * float(b[0]),)
    half = len(a) // 2
    a1, a2 = tuple(a[:half]), tuple(a[half:])
    b1, b2 = tuple(b[:half]), tuple(b[half:])
    left1 = cayley_dickson_multiply(a1, b1)
    left2 = cayley_dickson_multiply(_conjugate(b2), a2)
    right1 = cayley_dickson_multiply(b2, a1)
    right2 = cayley_dickson_multiply(a2, _conjugate(b1))
    return tuple(x - y for x, y in zip(left1, left2)) + tuple(x + y for x, y in zip(right1, right2))


def add(a: Sequence[float], b: Sequence[float]) -> tuple[float, ...]:
    if len(a) != len(b):
        raise ValueError("vector lengths differ")
    return tuple(float(x) + float(y) for x, y in zip(a, b))


def subtract(a: Sequence[float], b: Sequence[float]) -> tuple[float, ...]:
    if len(a) != len(b):
        raise ValueError("vector lengths differ")
    return tuple(float(x) - float(y) for x, y in zip(a, b))


def norm(a: Sequence[float]) -> float:
    return sqrt(sum(float(value) ** 2 for value in a))


def commutator(a: Sequence[float], b: Sequence[float]) -> tuple[float, ...]:
    return subtract(cayley_dickson_multiply(a, b), cayley_dickson_multiply(b, a))


def associator(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> tuple[float, ...]:
    return subtract(cayley_dickson_multiply(cayley_dickson_multiply(a, b), c), cayley_dickson_multiply(a, cayley_dickson_multiply(b, c)))


def basis(dimension: int, index: int) -> tuple[float, ...]:
    if dimension <= 0 or dimension & (dimension - 1):
        raise ValueError("dimension must be a positive power of two")
    if not 0 <= index < dimension:
        raise IndexError(index)
    return tuple(1.0 if i == index else 0.0 for i in range(dimension))


@dataclass(frozen=True)
class HypercomplexAudit:
    dimension: int
    max_commutator_norm: float
    max_associator_norm: float
    zero_divisor_candidates: tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]


def audit_basis(dimension: int = 16, search_zero_divisors: bool = True, max_candidates: int = 32) -> HypercomplexAudit:
    vectors = [basis(dimension, index) for index in range(dimension)]
    max_comm = 0.0
    max_assoc = 0.0
    for i in range(min(dimension, 16)):
        for j in range(min(dimension, 16)):
            max_comm = max(max_comm, norm(commutator(vectors[i], vectors[j])))
            for k in range(min(dimension, 8)):
                max_assoc = max(max_assoc, norm(associator(vectors[i], vectors[j], vectors[k])))
    candidates: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    if search_zero_divisors and dimension >= 16:
        signed_pairs: list[tuple[tuple[int, ...], tuple[float, ...]]] = []
        for i in range(1, dimension):
            for j in range(i + 1, dimension):
                signed_pairs.append(((i, j), add(vectors[i], vectors[j])))
                signed_pairs.append(((i, -j), subtract(vectors[i], vectors[j])))
        for (label_a, value_a), (label_b, value_b) in product(signed_pairs, repeat=2):
            if norm(value_a) == 0 or norm(value_b) == 0:
                continue
            if norm(cayley_dickson_multiply(value_a, value_b)) < 1e-12:
                candidates.append((label_a, label_b))
                if len(candidates) >= max_candidates:
                    break

    return HypercomplexAudit(dimension, max_comm, max_assoc, tuple(candidates))
