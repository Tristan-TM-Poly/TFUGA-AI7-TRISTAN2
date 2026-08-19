from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from .market import score_prime_asset
from .models import CandidateStatus, PrimeCandidate, PrimeCertificate
from .ntt import build_ntt_profile, verify_ntt_profile
from .primality import is_prime
from .proth import ProthProof, verify_proth_proof


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_certificate(
    candidate: PrimeCandidate,
    proof: ProthProof,
    *,
    independently_verified: bool = True,
    timestamp_utc: str | None = None,
    software_commit: str = "uncommitted",
) -> PrimeCertificate:
    if proof.n != candidate.value or not verify_proth_proof(proof.to_dict()):
        raise ValueError("proof does not certify candidate")
    if candidate.value >= 2**64 or not is_prime(candidate.value):
        raise ValueError("R0.1 certificate requires independent deterministic 64-bit verification")
    verified_candidate = replace(candidate, status=CandidateStatus.VERIFIED_PRIME, witness=proof.witness)
    ntt_profile = build_ntt_profile(candidate.value)
    score = score_prime_asset(
        verified_candidate,
        ntt_profile=ntt_profile,
        proven=True,
        independently_verified=independently_verified,
    )
    stamp = timestamp_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    certificate_id = f"omega-prime-{candidate.value:x}"
    certificate = PrimeCertificate(
        certificate_version="1.0",
        certificate_id=certificate_id,
        candidate=verified_candidate.to_dict(),
        proof=proof.to_dict(),
        verification={
            "deterministic_miller_rabin_64": True,
            "independently_verified": independently_verified,
            "ntt_profile": ntt_profile.to_dict(),
        },
        applications=["number-theoretic transform", "public modular arithmetic"],
        market_score=score.to_dict(),
        provenance={
            "generated_at_utc": stamp,
            "software": "omega_prime_value_t",
            "software_version": "0.1.0",
            "software_commit": software_commit,
            "expression": candidate.parameters.get("expression"),
        },
        oak={
            "status": "CERTIFIED_PUBLIC_ENGINEERING_PRIME_R0_1",
            "record_claimed": False,
            "novelty_claimed": False,
            "cryptographic_secret_material": False,
            "exclusive_ownership_of_number_claimed": False,
            "requires_external_precedence_search_for_novelty": True,
        },
    )
    unsigned = certificate.to_dict()
    unsigned["sha256"] = ""
    return replace(certificate, sha256=digest_payload(unsigned))


def verify_certificate(certificate: PrimeCertificate | dict[str, Any]) -> tuple[bool, list[str]]:
    payload = certificate.to_dict() if isinstance(certificate, PrimeCertificate) else dict(certificate)
    errors: list[str] = []
    expected_hash = payload.get("sha256", "")
    unsigned = dict(payload)
    unsigned["sha256"] = ""
    if digest_payload(unsigned) != expected_hash:
        errors.append("certificate sha256 mismatch")
    candidate = payload.get("candidate", {})
    try:
        value = int(candidate["value"])
    except (KeyError, TypeError, ValueError):
        return False, errors + ["candidate value missing or invalid"]
    if value >= 2**64 or not is_prime(value):
        errors.append("candidate is not a deterministic 64-bit prime")
    proof = payload.get("proof", {})
    if not verify_proth_proof(proof) or int(proof.get("n", -1)) != value:
        errors.append("invalid Proth proof")
    ntt_profile = payload.get("verification", {}).get("ntt_profile", {})
    if not verify_ntt_profile(ntt_profile) or int(ntt_profile.get("modulus", -1)) != value:
        errors.append("invalid NTT profile")
    if payload.get("oak", {}).get("record_claimed") is not False:
        errors.append("R0.1 certificates must not claim a record")
    return not errors, errors
