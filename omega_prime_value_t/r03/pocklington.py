from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from .canonical import sha256_hex
from .probable import probable_prime_receipt, verify_prime_factor


@dataclass(frozen=True, slots=True)
class PocklingtonFactor:
    prime: int
    exponent: int
    witness: int
    child_certificate: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PocklingtonCertificate:
    version: str
    n: int
    known_factor_product: int
    cofactor: int
    factors: tuple[PocklingtonFactor, ...]
    probable_prime_prefilter: dict[str, Any]
    oak: dict[str, Any]
    sha256: str = ""

    def unsigned_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["sha256"] = ""
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "n": self.n,
            "known_factor_product": self.known_factor_product,
            "cofactor": self.cofactor,
            "factors": [factor.to_dict() for factor in self.factors],
            "probable_prime_prefilter": self.probable_prime_prefilter,
            "oak": self.oak,
            "sha256": self.sha256,
        }


def _normalize_factorization(factorization: Mapping[int, int]) -> dict[int, int]:
    normalized: dict[int, int] = {}
    for raw_q, raw_e in factorization.items():
        q = int(raw_q)
        e = int(raw_e)
        if q < 2 or e < 1:
            raise ValueError("factorization requires prime >= 2 and exponent >= 1")
        normalized[q] = normalized.get(q, 0) + e
    if not normalized:
        raise ValueError("factorization must not be empty")
    return dict(sorted(normalized.items()))


def _known_product(factorization: Mapping[int, int]) -> int:
    product = 1
    for q, exponent in factorization.items():
        product *= q**exponent
    return product


def _find_witness(n: int, q: int, max_witness: int) -> int:
    for witness in range(2, max_witness + 1):
        if pow(witness, n - 1, n) != 1:
            continue
        gcd_value = math.gcd(pow(witness, (n - 1) // q, n) - 1, n)
        if gcd_value == 1:
            return witness
    raise ValueError(f"no Pocklington witness found for factor {q} up to {max_witness}")


def compile_pocklington_certificate(
    n: int,
    factorization: Mapping[int, int],
    *,
    child_certificates: Mapping[int, dict[str, Any]] | None = None,
    max_witness: int = 10_000,
) -> PocklingtonCertificate:
    if n < 3 or n % 2 == 0:
        raise ValueError("n must be an odd integer >= 3")
    normalized = _normalize_factorization(factorization)
    known_product = _known_product(normalized)
    if (n - 1) % known_product != 0:
        raise ValueError("known factor product must divide n - 1")
    if known_product <= math.isqrt(n):
        raise ValueError("Pocklington requires known factor product F > sqrt(n)")
    children = dict(child_certificates or {})
    factors: list[PocklingtonFactor] = []
    for q, exponent in normalized.items():
        child = children.get(q)
        if not verify_prime_factor(q, child):
            raise ValueError(f"factor {q} lacks a valid primality proof")
        factors.append(
            PocklingtonFactor(
                prime=q,
                exponent=exponent,
                witness=_find_witness(n, q, max_witness),
                child_certificate=child,
            )
        )
    prefilter = probable_prime_receipt(n).to_dict()
    if not bool(prefilter["probable_prime"]):
        raise ValueError("candidate failed probable-prime prefilter")
    certificate = PocklingtonCertificate(
        version="3.0",
        n=n,
        known_factor_product=known_product,
        cofactor=(n - 1) // known_product,
        factors=tuple(factors),
        probable_prime_prefilter=prefilter,
        oak={
            "status": "PROVEN_PRIME_BY_POCKLINGTON_R0_3",
            "proof_is_deterministic": True,
            "probable_prime_prefilter_is_not_the_proof": True,
            "novelty_claimed": False,
            "record_claimed": False,
            "economic_value_claimed": False,
        },
    )
    payload = certificate.to_dict()
    payload["sha256"] = ""
    return replace(certificate, sha256=sha256_hex(payload))


def verify_pocklington_certificate(certificate: PocklingtonCertificate | Mapping[str, Any]) -> tuple[bool, list[str]]:
    payload = certificate.to_dict() if isinstance(certificate, PocklingtonCertificate) else dict(certificate)
    errors: list[str] = []
    unsigned = dict(payload)
    expected_hash = str(unsigned.get("sha256", ""))
    unsigned["sha256"] = ""
    if sha256_hex(unsigned) != expected_hash:
        errors.append("certificate sha256 mismatch")
    try:
        n = int(payload["n"])
        known_product = int(payload["known_factor_product"])
        cofactor = int(payload["cofactor"])
        raw_factors = list(payload["factors"])
    except (KeyError, TypeError, ValueError):
        return False, errors + ["malformed certificate fields"]
    if n < 3 or n % 2 == 0:
        errors.append("n must be odd and >= 3")
    if known_product * cofactor != n - 1:
        errors.append("known product and cofactor do not reconstruct n - 1")
    if known_product <= math.isqrt(n):
        errors.append("known factor product does not exceed sqrt(n)")
    reconstructed = 1
    seen: set[int] = set()
    for raw in raw_factors:
        try:
            q = int(raw["prime"])
            exponent = int(raw["exponent"])
            witness = int(raw["witness"])
            child = raw.get("child_certificate")
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append("malformed factor proof")
            continue
        if q in seen:
            errors.append(f"duplicate factor {q}")
        seen.add(q)
        if exponent < 1:
            errors.append(f"invalid exponent for {q}")
            continue
        reconstructed *= q**exponent
        if not verify_prime_factor(q, child):
            errors.append(f"factor {q} is not proven prime")
        if pow(witness, n - 1, n) != 1:
            errors.append(f"Fermat condition failed for factor {q}")
        if math.gcd(pow(witness, (n - 1) // q, n) - 1, n) != 1:
            errors.append(f"gcd condition failed for factor {q}")
    if reconstructed != known_product:
        errors.append("factor list does not reconstruct known product")
    oak = payload.get("oak", {})
    if oak.get("novelty_claimed") is not False or oak.get("record_claimed") is not False:
        errors.append("R0.3 proof certificate may not claim novelty or a record")
    return not errors, errors
