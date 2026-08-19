from __future__ import annotations

from .models import MarketScore, NTTProfile, PrimeCandidate


def classify(total: float) -> str:
    if total >= 80:
        return "P4_platform_candidate"
    if total >= 65:
        return "P3_engineering_prime"
    if total >= 45:
        return "P2_specialized_record_candidate"
    if total >= 25:
        return "P1_certified_prime"
    return "P0_raw_prime"


def score_prime_asset(
    candidate: PrimeCandidate,
    *,
    ntt_profile: NTTProfile | None,
    proven: bool,
    independently_verified: bool,
    estimated_compute_seconds: float = 0.0,
) -> MarketScore:
    utility = 0.0
    if ntt_profile is not None:
        utility = min(30.0, 8.0 + 1.3 * ntt_profile.two_adicity)
    proof_quality = 22.0 if proven else 8.0
    if independently_verified:
        proof_quality += 8.0
    rarity = min(14.0, max(2.0, candidate.bit_length / 8.0))
    implementation = min(14.0, 4.0 + (candidate.bit_length in (32, 64, 128, 256)) * 6.0)
    provenance = 10.0 if independently_verified else 6.0
    cost_penalty = min(12.0, estimated_compute_seconds / 60.0)
    risk_penalty = 0.0 if proven else 15.0
    total = max(
        0.0,
        utility + proof_quality + rarity + implementation + provenance - cost_penalty - risk_penalty,
    )
    return MarketScore(
        total=round(total, 3),
        utility=round(utility, 3),
        proof_quality=round(proof_quality, 3),
        rarity=round(rarity, 3),
        implementation=round(implementation, 3),
        provenance=round(provenance, 3),
        cost_penalty=round(cost_penalty, 3),
        risk_penalty=round(risk_penalty, 3),
        classification=classify(total),
    )
