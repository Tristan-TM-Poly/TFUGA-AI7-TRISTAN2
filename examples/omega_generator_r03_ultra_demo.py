"""Demonstrate Ω-GENERATOR-DISCOVERY R0.3 Ultra queries and audits."""
from __future__ import annotations

import json

from omega_generator_discovery_t.ultra_catalog import (
    audit_ultra_catalog,
    catalog_statistics,
    deterministic_validation_sample,
    query_generators,
    related_bundle,
)


def main() -> None:
    spectral = query_generators(
        domain="spectral",
        family="translation",
        scale="micro",
        representation="operator",
        regime="local_linear",
        limit=8,
    )
    high_risk_sample = deterministic_validation_sample(modulus=64, residue=0)
    result = {
        "audit": audit_ultra_catalog().to_dict(),
        "statistics": catalog_statistics(),
        "spectral_translation_candidates": [record.to_dict() for record in spectral],
        "first_linked_bundle": related_bundle(spectral[0].id) if spectral else None,
        "validation_sample": {
            "count": len(high_risk_sample),
            "first_ids": list(high_risk_sample[:16]),
            "policy": "all_high_risk_plus_deterministic_stratified_sample",
        },
        "oak_boundary": (
            "Generated candidates and tests are research infrastructure, not "
            "empirical evidence or certified laws."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
