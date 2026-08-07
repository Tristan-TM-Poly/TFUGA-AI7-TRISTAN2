from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, asdict
from typing import Iterable

_DETERMINISTIC_U64_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
_SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


@dataclass(frozen=True, slots=True)
class ProbablePrimeReceipt:
    value: int
    probable_prime: bool
    rounds: int
    bases: tuple[int, ...]
    deterministic_domain: str | None
    divisor: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _decompose(n_minus_one: int) -> tuple[int, int]:
    d = n_minus_one
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2
    return s, d


def _is_strong_probable_prime(n: int, base: int) -> bool:
    if base % n == 0:
        return True
    s, d = _decompose(n - 1)
    x = pow(base, d, n)
    if x in (1, n - 1):
        return True
    for _ in range(s - 1):
        x = (x * x) % n
        if x == n - 1:
            return True
    return False


def deterministic_bases(n: int, rounds: int) -> tuple[int, ...]:
    if n < 2**64:
        return tuple(base for base in _DETERMINISTIC_U64_BASES if base % n)
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    seed = n.to_bytes((n.bit_length() + 7) // 8, "big")
    bases: list[int] = []
    counter = 0
    while len(bases) < rounds:
        digest = hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        base = 2 + int.from_bytes(digest, "big") % (n - 3)
        if base not in bases:
            bases.append(base)
        counter += 1
    return tuple(bases)


def probable_prime_receipt(n: int, rounds: int = 24) -> ProbablePrimeReceipt:
    if n < 2:
        return ProbablePrimeReceipt(n, False, 0, (), "u64" if n < 2**64 else None)
    for prime in _SMALL_PRIMES:
        if n == prime:
            return ProbablePrimeReceipt(n, True, 0, (), "u64")
        if n % prime == 0:
            return ProbablePrimeReceipt(n, False, 0, (), "u64" if n < 2**64 else None, prime)
    root = math.isqrt(n)
    if root * root == n:
        return ProbablePrimeReceipt(n, False, 0, (), "u64" if n < 2**64 else None, root)
    bases = deterministic_bases(n, rounds)
    for base in bases:
        if not _is_strong_probable_prime(n, base):
            return ProbablePrimeReceipt(
                n,
                False,
                len(bases),
                bases,
                "u64-deterministic" if n < 2**64 else None,
            )
    return ProbablePrimeReceipt(
        n,
        True,
        len(bases),
        bases,
        "u64-deterministic" if n < 2**64 else None,
    )


def is_prime_u64(n: int) -> bool:
    if not 0 <= n < 2**64:
        raise ValueError("is_prime_u64 requires 0 <= n < 2**64")
    return probable_prime_receipt(n).probable_prime


def verify_prime_factor(q: int, child_certificate: dict[str, object] | None = None) -> bool:
    if q < 2**64:
        return is_prime_u64(q)
    if child_certificate is None:
        return False
    from .pocklington import verify_pocklington_certificate

    ok, _ = verify_pocklington_certificate(child_certificate)
    return ok and int(child_certificate.get("n", -1)) == q
