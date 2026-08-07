from __future__ import annotations

from dataclasses import replace

from .models import CandidateStatus, PrimeCandidate


def primes_up_to(limit: int) -> list[int]:
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            start = p * p
            sieve[start : limit + 1 : p] = b"\x00" * (((limit - start) // p) + 1)
    return [index for index, flag in enumerate(sieve) if flag]


def screen_candidate(candidate: PrimeCandidate, sieve_bound: int = 10_000) -> PrimeCandidate:
    for prime in primes_up_to(sieve_bound):
        if candidate.value == prime:
            return candidate
        if candidate.value % prime == 0:
            return replace(
                candidate,
                status=CandidateStatus.FILTERED_COMPOSITE,
                small_factor=prime,
                notes=candidate.notes + (f"small factor {prime}",),
            )
    return candidate
