from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from typing import Any, Iterator, Mapping

from ..r03.canonical import sha256_hex


def primes_up_to(limit: int) -> tuple[int, ...]:
    if limit < 2:
        return ()
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for value in range(2, math.isqrt(limit) + 1):
        if sieve[value]:
            sieve[value * value : limit + 1 : value] = b"\x00" * (((limit - value * value) // value) + 1)
    return tuple(index for index, is_prime in enumerate(sieve) if is_prime)


@dataclass(frozen=True, slots=True)
class ResidueRule:
    exponent: int
    divisor: int
    forbidden_residue: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResidueProgram:
    version: str
    exponent_min: int
    exponent_max: int
    prime_bound: int
    rules: tuple[ResidueRule, ...]
    oak: dict[str, Any]
    sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "exponent_min": self.exponent_min,
            "exponent_max": self.exponent_max,
            "prime_bound": self.prime_bound,
            "rules": [rule.to_dict() for rule in self.rules],
            "oak": self.oak,
            "sha256": self.sha256,
        }


def compile_proth_residue_program(
    exponent_min: int,
    exponent_max: int,
    *,
    prime_bound: int = 10_000,
) -> ResidueProgram:
    if exponent_min < 1 or exponent_max < exponent_min:
        raise ValueError("invalid exponent interval")
    if prime_bound < 3:
        raise ValueError("prime_bound must be >= 3")
    rules: list[ResidueRule] = []
    for exponent in range(exponent_min, exponent_max + 1):
        for divisor in primes_up_to(prime_bound):
            if divisor == 2:
                continue
            power = pow(2, exponent, divisor)
            forbidden = (-pow(power, -1, divisor)) % divisor
            rules.append(ResidueRule(exponent, divisor, forbidden))
    program = ResidueProgram(
        version="4.0",
        exponent_min=exponent_min,
        exponent_max=exponent_max,
        prime_bound=prime_bound,
        rules=tuple(rules),
        oak={
            "status": "COMPILED_PROTH_RESIDUE_FILTER_R0_4",
            "filter_is_not_primality_proof": True,
            "survivor_is_not_probable_prime_claim": True,
            "novelty_claimed": False,
        },
    )
    payload = program.to_dict()
    payload["sha256"] = ""
    return replace(program, sha256=sha256_hex(payload))


def verify_residue_program(program: ResidueProgram | Mapping[str, Any]) -> tuple[bool, list[str]]:
    payload = program.to_dict() if isinstance(program, ResidueProgram) else dict(program)
    errors: list[str] = []
    unsigned = dict(payload)
    expected = str(unsigned.get("sha256", ""))
    unsigned["sha256"] = ""
    if sha256_hex(unsigned) != expected:
        errors.append("residue program sha256 mismatch")
    try:
        exponent_min = int(payload["exponent_min"])
        exponent_max = int(payload["exponent_max"])
        prime_bound = int(payload["prime_bound"])
        rules = list(payload["rules"])
    except (KeyError, TypeError, ValueError):
        return False, errors + ["malformed residue program"]
    expected_rules = compile_proth_residue_program(exponent_min, exponent_max, prime_bound=prime_bound)
    if rules != [rule.to_dict() for rule in expected_rules.rules]:
        errors.append("residue rules do not match compiler output")
    if payload.get("oak", {}).get("novelty_claimed") is not False:
        errors.append("residue program may not claim novelty")
    return not errors, errors


def _rules_for(program: ResidueProgram | Mapping[str, Any], exponent: int) -> tuple[tuple[int, int], ...]:
    payload = program.to_dict() if isinstance(program, ResidueProgram) else dict(program)
    exponent_min = int(payload["exponent_min"])
    exponent_max = int(payload["exponent_max"])
    if not exponent_min <= exponent <= exponent_max:
        raise ValueError("exponent is outside the compiled program interval")
    return tuple(
        (int(rule["divisor"]), int(rule["forbidden_residue"]))
        for rule in payload["rules"]
        if int(rule["exponent"]) == exponent
    )


def candidate_survives(program: ResidueProgram | Mapping[str, Any], exponent: int, k: int) -> bool:
    if k <= 0 or k % 2 == 0 or k >= 2**exponent:
        return False
    return all(k % divisor != residue for divisor, residue in _rules_for(program, exponent))


def segmented_survivors(
    program: ResidueProgram | Mapping[str, Any],
    exponent: int,
    k_start: int,
    k_stop: int,
    *,
    segment_size: int = 65_536,
) -> Iterator[int]:
    if segment_size <= 0:
        raise ValueError("segment_size must be positive")
    if k_stop < k_start:
        raise ValueError("k_stop must be >= k_start")
    lower = max(1, k_start)
    upper = min(k_stop, 2**exponent - 1)
    rules = _rules_for(program, exponent)
    segment_begin = lower
    while segment_begin <= upper:
        segment_end = min(upper, segment_begin + segment_size - 1)
        first_odd = segment_begin | 1
        candidates = bytearray(b"\x01") * (((segment_end - first_odd) // 2) + 1) if first_odd <= segment_end else bytearray()
        for divisor, forbidden in rules:
            first = first_odd + ((forbidden - first_odd) % divisor)
            if first % 2 == 0:
                first += divisor
            step = 2 * divisor
            for value in range(first, segment_end + 1, step):
                candidates[(value - first_odd) // 2] = 0
        for index, alive in enumerate(candidates):
            if alive:
                yield first_odd + 2 * index
        segment_begin = segment_end + 1


def filter_receipt(
    program: ResidueProgram | Mapping[str, Any],
    exponent: int,
    k_start: int,
    k_stop: int,
    *,
    segment_size: int = 65_536,
) -> dict[str, Any]:
    survivors = tuple(segmented_survivors(program, exponent, k_start, k_stop, segment_size=segment_size))
    odd_total = sum(1 for k in range(max(1, k_start), min(k_stop, 2**exponent - 1) + 1) if k % 2)
    return {
        "exponent": exponent,
        "k_start": k_start,
        "k_stop": k_stop,
        "segment_size": segment_size,
        "odd_candidates": odd_total,
        "survivors": len(survivors),
        "rejected": odd_total - len(survivors),
        "survivor_values": list(survivors),
        "program_sha256": (program.sha256 if isinstance(program, ResidueProgram) else str(program["sha256"])),
        "oak": {
            "filter_only": True,
            "primality_claimed": False,
            "novelty_claimed": False,
        },
    }
