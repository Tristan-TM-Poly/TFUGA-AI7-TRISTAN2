from __future__ import annotations

from collections.abc import Iterable


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def v2(n: int) -> int:
    """Return the exponent of 2 dividing positive integer n."""
    if n <= 0:
        raise ValueError("v2 is defined here only for positive integers")
    return (n & -n).bit_length() - 1


def factor_out_twos(n: int) -> tuple[int, int]:
    exponent = v2(n)
    return n >> exponent, exponent


def jacobi(a: int, n: int) -> int:
    """Compute the Jacobi symbol (a/n) for positive odd n."""
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be a positive odd integer")
    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n
    return result if n == 1 else 0


def trial_factor(n: int, limit: int = 100_000) -> int | None:
    """Return a small factor, or None when no factor <= limit is found."""
    if n < 2:
        return None
    if n % 2 == 0:
        return 2 if n != 2 else None
    divisor = 3
    maximum = min(limit, int(n**0.5))
    while divisor <= maximum:
        if n % divisor == 0:
            return divisor
        divisor += 2
    return None


def distinct_prime_factors(n: int) -> list[int]:
    """Trial-factor n into distinct prime factors; intended for machine-size p-1."""
    if n <= 0:
        raise ValueError("n must be positive")
    factors: list[int] = []
    if n % 2 == 0:
        factors.append(2)
        while n % 2 == 0:
            n //= 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            factors.append(divisor)
            while n % divisor == 0:
                n //= divisor
        divisor += 2
    if n > 1:
        factors.append(n)
    return factors


def product(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result *= value
    return result
