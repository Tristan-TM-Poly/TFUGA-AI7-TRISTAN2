from __future__ import annotations

from .campaign import PrimeCampaign, SearchPolicy
from .certificate import verify_certificate


def deterministic_benchmark() -> dict[str, object]:
    policies = [
        SearchPolicy(exponent=8, k_min=1, k_max=255, max_results=8),
        SearchPolicy(exponent=16, k_min=1, k_max=255, max_results=8),
        SearchPolicy(exponent=23, k_min=1, k_max=255, max_results=8),
    ]
    reports = [PrimeCampaign(policy).run().to_dict() for policy in policies]
    certificate_count = sum(len(report["certificates"]) for report in reports)
    verified = 0
    for report in reports:
        for certificate in report["certificates"]:
            ok, _ = verify_certificate(certificate)
            verified += int(ok)
    return {
        "status": "CERTIFIED_PUBLIC_ENGINEERING_PRIME_FIXTURES_R0_1",
        "campaigns": reports,
        "certificate_count": certificate_count,
        "verified_certificate_count": verified,
        "all_certificates_verified": certificate_count == verified and certificate_count > 0,
        "claims": {
            "new_world_record_claimed": False,
            "novel_prime_claimed": False,
            "economic_value_guaranteed": False,
            "cryptographic_secret_generation_claimed": False,
        },
    }
