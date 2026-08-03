from __future__ import annotations

from .arithmetic import factor_out_twos

_SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
# Deterministic for every unsigned 64-bit integer.
_MR_BASES_64 = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)


def _miller_rabin_round(n: int, base: int, odd_part: int, twos: int) -> bool:
    base %= n
    if base in (0, 1):
        return True
    x = pow(base, odd_part, n)
    if x in (1, n - 1):
        return True
    for _ in range(twos - 1):
        x = x * x % n
        if x == n - 1:
            return True
    return False


def is_probable_prime(n: int, bases: tuple[int, ...] | None = None) -> bool:
    if n < 2:
        return False
    for prime in _SMALL_PRIMES:
        if n == prime:
            return True
        if n % prime == 0:
            return False
    odd_part, twos = factor_out_twos(n - 1)
    selected = bases or (_MR_BASES_64 if n < 2**64 else _SMALL_PRIMES)
    return all(_miller_rabin_round(n, base, odd_part, twos) for base in selected)


def is_prime(n: int) -> bool:
    """Deterministic for n < 2**64; PRP-only beyond that boundary."""
    if n >= 2**64:
        raise ValueError("deterministic is_prime is limited to unsigned 64-bit integers")
    return is_probable_prime(n)


def primality_status(n: int) -> str:
    if n < 2**64:
        return "proven_by_deterministic_miller_rabin_64" if is_prime(n) else "composite"
    return "probable_prime" if is_probable_prime(n) else "composite"
