"""PrimeTensor and GapTensor utilities for Ω-MATH-TRISTAN.

These functions are intentionally conservative: they extract arithmetic
signatures and features, but they do not claim to predict primes or prove prime
structure. Pattern discovery must be routed through OAK and baseline tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt
from statistics import mean
from typing import Callable, Iterable


def is_prime(n: int) -> bool:
    """Return True if n is prime using trial division."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    limit = int(sqrt(n)) + 1
    for divisor in range(3, limit, 2):
        if n % divisor == 0:
            return False
    return True


def first_primes(count: int) -> list[int]:
    """Return the first `count` prime numbers."""
    if count < 0:
        raise ValueError("count must be non-negative")
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if is_prime(candidate):
            primes.append(candidate)
        candidate += 1 if candidate == 2 else 2
    return primes


def primorial(primes: Iterable[int]) -> int:
    """Return the product of the provided primes."""
    product = 1
    for prime in primes:
        product *= prime
    return product


def residue_signature(prime: int, previous_primes: Iterable[int]) -> tuple[int, ...]:
    """Return `(prime mod p_j)` over previous primes.

    For a prime not in previous_primes, all entries should be non-zero.
    """
    return tuple(prime % p for p in previous_primes)


def residue_signature_by_index(primes: list[int], index: int) -> tuple[int, ...]:
    """Return the residue signature of `primes[index]` against earlier primes."""
    if index < 0 or index >= len(primes):
        raise IndexError("index outside prime list")
    return residue_signature(primes[index], primes[:index])


def mixed_radix_primorial_coordinates(value: int, bases: Iterable[int]) -> tuple[int, ...]:
    """Return mixed-radix coordinates for `value` in the supplied bases.

    For bases p_1, p_2, ..., coordinates are:
    floor(value / P_{j-1}) mod p_j where P_{j-1}=product of previous bases.
    """
    coords: list[int] = []
    place = 1
    for base in bases:
        if base <= 1:
            raise ValueError("mixed-radix bases must be > 1")
        coords.append((value // place) % base)
        place *= base
    return tuple(coords)


def gap_sequence(primes: list[int], offset: int = 1) -> list[int]:
    """Return gaps p_{i+offset} - p_i."""
    if offset <= 0:
        raise ValueError("offset must be positive")
    if offset >= len(primes):
        return []
    return [primes[i + offset] - primes[i] for i in range(len(primes) - offset)]


def gap_feature_vector(gap: int, anchor_prime: int, moduli: Iterable[int] = (2, 3, 5, 7, 11)) -> tuple[float, ...]:
    """Return a compact CVCD-style feature vector for a prime gap."""
    if gap < 0:
        raise ValueError("gap must be non-negative")
    if anchor_prime < 2:
        raise ValueError("anchor_prime should be at least 2")
    residues = [float(gap % modulus) for modulus in moduli]
    normalized = gap / max(log(anchor_prime + 1), 1e-12)
    return (float(gap), *residues, normalized)


def gap_tensor_features(primes: list[int], max_offset: int = 3, moduli: Iterable[int] = (2, 3, 5, 7, 11)) -> dict[tuple[int, int], tuple[float, ...]]:
    """Return features keyed by `(i, offset)` for prime gaps."""
    if max_offset <= 0:
        raise ValueError("max_offset must be positive")
    features: dict[tuple[int, int], tuple[float, ...]] = {}
    for offset in range(1, max_offset + 1):
        for i in range(0, max(0, len(primes) - offset)):
            gap = primes[i + offset] - primes[i]
            features[(i, offset)] = gap_feature_vector(gap, primes[i], moduli=moduli)
    return features


def signature_entropy_proxy(signature: Iterable[int]) -> float:
    """Return a simple normalized diversity proxy for a residue signature.

    This is not Shannon entropy. It is a lightweight dependency-free diversity
    indicator: unique_count / length.
    """
    values = tuple(signature)
    if not values:
        return 0.0
    return len(set(values)) / len(values)


@dataclass(frozen=True)
class PrimeTensorReport:
    """Summary report for a finite prime sample."""

    prime_count: int
    max_prime: int | None
    average_gap: float
    max_gap: int | None
    average_signature_diversity: float
    oak_warning: str = "Patterns in finite prime samples are experimental signatures, not theorems."


def summarize_prime_sample(primes: list[int]) -> PrimeTensorReport:
    """Return a compact report for the provided prime sample."""
    gaps = gap_sequence(primes, 1)
    diversities = [signature_entropy_proxy(residue_signature_by_index(primes, i)) for i in range(len(primes))]
    return PrimeTensorReport(
        prime_count=len(primes),
        max_prime=max(primes) if primes else None,
        average_gap=mean(gaps) if gaps else 0.0,
        max_gap=max(gaps) if gaps else None,
        average_signature_diversity=mean(diversities) if diversities else 0.0,
    )


def compare_to_sequence_baseline(values: list[int], baseline: list[int], feature: Callable[[list[int]], float]) -> float:
    """Return feature(values) - feature(baseline).

    This tiny helper enforces the OAK habit: pattern claims should be compared
    against a baseline rather than inspected in isolation.
    """
    if not values or not baseline:
        raise ValueError("values and baseline must be non-empty")
    return feature(values) - feature(baseline)
