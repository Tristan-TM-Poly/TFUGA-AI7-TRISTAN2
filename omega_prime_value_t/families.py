from __future__ import annotations

from collections.abc import Iterator

from .models import PrimeCandidate


def proth_number(k: int, n: int) -> int:
    if n < 1:
        raise ValueError("n must be positive")
    if k <= 0 or k % 2 == 0:
        raise ValueError("k must be a positive odd integer")
    if k >= 2**n:
        raise ValueError("Proth form requires k < 2**n")
    return k * (2**n) + 1


def iter_proth_candidates(
    n: int,
    k_min: int = 1,
    k_max: int | None = None,
    *,
    max_value: int | None = None,
) -> Iterator[PrimeCandidate]:
    if n < 1:
        raise ValueError("n must be positive")
    upper = min(k_max if k_max is not None else 2**n - 1, 2**n - 1)
    start = max(1, k_min)
    if start % 2 == 0:
        start += 1
    for k in range(start, upper + 1, 2):
        value = k * (2**n) + 1
        if max_value is not None and value > max_value:
            break
        yield PrimeCandidate(
            value=value,
            family="proth",
            parameters={"k": k, "n": n, "expression": f"{k}*2^{n}+1"},
            notes=("public engineering-prime candidate",),
        )


def pseudo_mersenne_candidate(bits: int, c: int) -> PrimeCandidate:
    if bits < 2 or c <= 0:
        raise ValueError("bits >= 2 and c > 0 are required")
    value = 2**bits - c
    return PrimeCandidate(
        value=value,
        family="pseudo_mersenne",
        parameters={"bits": bits, "c": c, "expression": f"2^{bits}-{c}"},
    )


def safe_prime_candidate(q: int) -> PrimeCandidate:
    return PrimeCandidate(
        value=2 * q + 1,
        family="safe_prime",
        parameters={"q": q, "expression": f"2*{q}+1"},
    )
