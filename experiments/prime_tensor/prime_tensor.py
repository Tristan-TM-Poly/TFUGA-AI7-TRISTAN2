"""Prime Tensor proof-sprint utilities.

This module is intentionally dependency-free. It supports the mathematical canon
entry:

    P[i, j] = p_i mod p_j, j < i

and demonstrates CRT reconstruction for the triangular prime residue signature.

OAK guardrail:
    This proves an encoding/reconstruction property only. It does not prove any
    global conjecture about prime distribution.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import gcd
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class PrimeSignature:
    """Triangular residue signature for one prime."""

    index_1based: int
    prime: int
    moduli: Tuple[int, ...]
    residues: Tuple[int, ...]

    @property
    def primorial_modulus(self) -> int:
        product = 1
        for modulus in self.moduli:
            product *= modulus
        return product


def first_primes(count: int) -> List[int]:
    """Return the first `count` primes by trial division.

    The function is small and deterministic so the proof sprint can run in CI
    without external dependencies.
    """

    if count < 0:
        raise ValueError("count must be non-negative")

    primes: List[int] = []
    candidate = 2
    while len(primes) < count:
        is_prime = True
        for prime in primes:
            if prime * prime > candidate:
                break
            if candidate % prime == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1 if candidate == 2 else 2
    return primes


def triangular_signature(primes: Sequence[int], index_0based: int) -> PrimeSignature:
    """Build the residue signature of primes[index_0based]."""

    if index_0based < 0 or index_0based >= len(primes):
        raise IndexError("index_0based is outside the prime list")

    prime = primes[index_0based]
    moduli = tuple(primes[:index_0based])
    residues = tuple(prime % modulus for modulus in moduli)
    return PrimeSignature(
        index_1based=index_0based + 1,
        prime=prime,
        moduli=moduli,
        residues=residues,
    )


def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = _extended_gcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def _mod_inverse(a: int, modulus: int) -> int:
    g, x, _ = _extended_gcd(a, modulus)
    if g != 1:
        raise ValueError(f"{a} has no inverse modulo {modulus}")
    return x % modulus


def crt(residues: Sequence[int], moduli: Sequence[int]) -> Tuple[int, int]:
    """Chinese Remainder Theorem for pairwise-coprime moduli.

    Returns `(solution, modulus_product)` with solution in [0, modulus_product).
    """

    if len(residues) != len(moduli):
        raise ValueError("residues and moduli must have the same length")
    if not residues:
        return (0, 1)

    solution = 0
    modulus_product = 1
    for residue, modulus in zip(residues, moduli):
        if modulus <= 1:
            raise ValueError("all moduli must be > 1")
        if gcd(modulus_product, modulus) != 1:
            raise ValueError("moduli must be pairwise coprime")

        # Solve solution + modulus_product * t = residue (mod modulus)
        delta = (residue - solution) % modulus
        t = (delta * _mod_inverse(modulus_product % modulus, modulus)) % modulus
        solution += modulus_product * t
        modulus_product *= modulus
        solution %= modulus_product

    return solution, modulus_product


def reconstruct_from_signature(signature: PrimeSignature) -> int:
    """Reconstruct the prime from its triangular residue signature.

    For signatures with at least three previous moduli (i >= 4 in 1-based
    indexing), the CRT solution is exactly the prime because p_i is below the
    primorial modulus.
    """

    solution, modulus_product = crt(signature.residues, signature.moduli)
    if signature.index_1based >= 4 and not (0 < signature.prime < modulus_product):
        raise AssertionError("Prime Tensor size condition failed")
    return solution


def prime_tensor(count: int) -> List[PrimeSignature]:
    primes = first_primes(count)
    return [triangular_signature(primes, i) for i in range(count)]


def gap_tensor_rows(primes: Sequence[int], max_step: int = 3) -> List[dict]:
    """Return small modular gap tensor rows.

    Each row contains G[i, n] = p[i+n] - p[i] and residues of that gap modulo
    previous prime bases.
    """

    rows: List[dict] = []
    for i, prime in enumerate(primes):
        for step in range(1, max_step + 1):
            j = i + step
            if j >= len(primes):
                continue
            gap = primes[j] - prime
            moduli = tuple(primes[: max(0, i)])
            rows.append(
                {
                    "index_1based": i + 1,
                    "step": step,
                    "prime": prime,
                    "future_prime": primes[j],
                    "gap": gap,
                    "residues": [gap % modulus for modulus in moduli],
                    "moduli": list(moduli),
                }
            )
    return rows


def oak_report(count: int = 16) -> dict:
    """Build a small OAK report for the Prime Tensor proof sprint."""

    signatures = prime_tensor(count)
    checked = []
    failures = []
    for signature in signatures:
        reconstructed = reconstruct_from_signature(signature)
        exact_scope = signature.index_1based >= 4
        ok = (reconstructed == signature.prime) if exact_scope else True
        entry = {
            "index_1based": signature.index_1based,
            "prime": signature.prime,
            "signature_length": len(signature.residues),
            "primorial_modulus": signature.primorial_modulus,
            "reconstructed": reconstructed,
            "exact_scope_i_ge_4": exact_scope,
            "ok": ok,
        }
        checked.append(entry)
        if not ok:
            failures.append(entry)

    return {
        "module": "Prime Tensor CRT Reconstruction",
        "status": "PROVED_LOCAL" if not failures else "M_MINUS",
        "count": count,
        "checked": checked,
        "failures": failures,
        "guardrails": [
            "Encoding/reconstruction is proven only under the stated CRT and size conditions.",
            "No claim is made about Riemann, Goldbach or twin primes.",
            "Statistical usefulness requires separate randomized controls and benchmarks.",
        ],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prime Tensor CRT proof sprint")
    parser.add_argument("--count", type=int, default=16, help="number of primes to inspect")
    parser.add_argument("--max-gap-step", type=int, default=3, help="gap tensor horizon")
    args = parser.parse_args(list(argv) if argv is not None else None)

    primes = first_primes(args.count)
    report = oak_report(args.count)
    payload = {
        "primes": primes,
        "oak_report": report,
        "gap_tensor": gap_tensor_rows(primes, max_step=args.max_gap_step),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
