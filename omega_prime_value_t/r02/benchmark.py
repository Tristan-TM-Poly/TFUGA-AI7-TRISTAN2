from __future__ import annotations

import tempfile
from pathlib import Path

from ..certificate import verify_certificate
from .engine import CampaignEngine
from .ntt_kernel import validate_convolution
from .planner import CampaignPlanner, PlannerPolicy, verify_manifest
from .portfolio import PortfolioAllocator
from .registry import LocalPrimeRegistry
from .storage import CampaignStore


def deterministic_benchmark() -> dict[str, object]:
    manifest = CampaignPlanner(
        PlannerPolicy(exponent_min=8, exponent_max=10, k_min=1, k_max=127, shard_size=17)
    ).build()
    with tempfile.TemporaryDirectory(prefix="omega-prime-r02-") as directory:
        database = Path(directory) / "campaign.sqlite3"
        with CampaignStore(database) as store:
            engine = CampaignEngine(store, sieve_bound=500)
            first = engine.execute(manifest, max_tasks=37)
            checkpoint_after_first = store.checkpoint(manifest.campaign_id)
            second = engine.execute(manifest)
            checkpoint_final = store.checkpoint(manifest.campaign_id)
            certificates = store.certificate_payloads(manifest.campaign_id)
            verified = [verify_certificate(certificate)[0] for certificate in certificates]
            registry = LocalPrimeRegistry(store)
            database_evidence = {
                "integrity_check": store.integrity_check(),
                "event_count": store.event_count(manifest.campaign_id),
                "registry_count": registry.count(),
                "certificate_count": len(certificates),
            }
    allocator = PortfolioAllocator()
    observations = [
        ("prestige", 0.2, 4.0),
        ("research", 2.0, 2.0),
        ("product", 5.0, 2.0),
        ("product", 4.0, 1.5),
        ("research", 1.5, 1.0),
        ("prestige", 0.0, 3.0),
    ]
    for name, reward, cost in observations:
        allocator.observe(name, reward, cost)
    convolution_evidence = validate_convolution(
        [1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12],
        998244353,
    )
    return {
        "status": "CERTIFIED_RESUMABLE_PRIME_CAMPAIGN_FIXTURES_R0_2",
        "manifest": manifest.to_dict(),
        "manifest_verified": verify_manifest(manifest),
        "first_pass": first.to_dict(),
        "second_pass": second.to_dict(),
        "checkpoint_after_first": checkpoint_after_first,
        "checkpoint_final": checkpoint_final,
        "database": database_evidence,
        "all_certificates_verified": bool(certificates) and all(verified),
        "ntt_convolution": convolution_evidence,
        "portfolio": allocator.report(),
        "claims": {
            "campaign_is_infinite": False,
            "external_novelty_checked": False,
            "record_claimed": False,
            "market_demand_proven": False,
            "secret_prime_material_generated": False,
        },
    }
