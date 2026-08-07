from __future__ import annotations

from .probable import is_prime_u64

MODULUS = 998244353
PRIMITIVE_ROOT = 3


def mod_pow(base: int, exponent: int, modulus: int) -> int:
    if modulus <= 0 or exponent < 0:
        raise ValueError("positive modulus and nonnegative exponent required")
    return pow(base, exponent, modulus)


def ntt(values: list[int], invert: bool = False, modulus: int = MODULUS, primitive_root: int = PRIMITIVE_ROOT) -> list[int]:
    n = len(values)
    if n == 0 or n & (n - 1):
        raise ValueError("NTT length must be a positive power of two")
    if (modulus - 1) % n:
        raise ValueError("NTT length must divide modulus - 1")
    output = [value % modulus for value in values]
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            output[i], output[j] = output[j], output[i]
    length = 2
    while length <= n:
        root = pow(primitive_root, (modulus - 1) // length, modulus)
        if invert:
            root = pow(root, modulus - 2, modulus)
        for start in range(0, n, length):
            omega = 1
            half = length // 2
            for offset in range(half):
                even = output[start + offset]
                odd = output[start + offset + half] * omega % modulus
                output[start + offset] = (even + odd) % modulus
                output[start + offset + half] = (even - odd) % modulus
                omega = omega * root % modulus
        length *= 2
    if invert:
        inverse_n = pow(n, modulus - 2, modulus)
        output = [value * inverse_n % modulus for value in output]
    return output


def convolution(left: list[int], right: list[int]) -> list[int]:
    if not left or not right:
        return []
    size = 1
    needed = len(left) + len(right) - 1
    while size < needed:
        size <<= 1
    a = left + [0] * (size - len(left))
    b = right + [0] * (size - len(right))
    fa = ntt(a)
    fb = ntt(b)
    result = ntt([(x * y) % MODULUS for x, y in zip(fa, fb)], invert=True)
    return result[:needed]


def kernel_vectors() -> dict[str, object]:
    primes = [2, 3, 5, 17, 97, 998244353, 18446744073709551557]
    composites = [0, 1, 4, 9, 341, 561, 18446744073709551615]
    left = [1, 2, 3, 4, 5]
    right = [7, 11, 13]
    return {
        "primality": {str(value): is_prime_u64(value) for value in primes + composites},
        "mod_pow": mod_pow(123456789, 12345, MODULUS),
        "convolution": convolution(left, right),
    }
