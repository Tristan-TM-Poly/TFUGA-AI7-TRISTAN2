from __future__ import annotations

from .arithmetic import distinct_prime_factors, v2
from .models import NTTProfile
from .primality import is_prime


def primitive_root(prime: int) -> int:
    if prime >= 2**64 or not is_prime(prime):
        raise ValueError("primitive_root requires a proven prime below 2**64")
    phi = prime - 1
    factors = distinct_prime_factors(phi)
    for candidate in range(2, prime):
        if all(pow(candidate, phi // factor, prime) != 1 for factor in factors):
            return candidate
    raise RuntimeError("primitive root not found")


def build_ntt_profile(prime: int) -> NTTProfile:
    two_adicity = v2(prime - 1)
    if two_adicity < 1:
        raise ValueError("prime-1 must be divisible by 2")
    generator = primitive_root(prime)
    length = 2**two_adicity
    root = pow(generator, (prime - 1) // length, prime)
    if pow(root, length, prime) != 1:
        raise AssertionError("computed root does not close")
    if length > 1 and pow(root, length // 2, prime) == 1:
        raise AssertionError("computed root is not primitive")
    return NTTProfile(prime, two_adicity, generator, root, length)


def verify_ntt_profile(profile: dict[str, int]) -> bool:
    try:
        p = int(profile["modulus"])
        adicity = int(profile["two_adicity"])
        root = int(profile["root_of_unity"])
        length = int(profile["maximum_transform_length"])
    except (KeyError, TypeError, ValueError):
        return False
    if length != 2**adicity or (p - 1) % length != 0:
        return False
    return pow(root, length, p) == 1 and (length == 1 or pow(root, length // 2, p) != 1)
