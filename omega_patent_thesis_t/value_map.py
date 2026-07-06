"""Value hypothesis map."""

from __future__ import annotations

from .risk import risk_level
from .seed import PatentThesisSeed


def value_map(seed: PatentThesisSeed) -> dict:
    seed.validate()
    return {
        "patent_id": seed.patent_id,
        "status": seed.status,
        "risk_level": risk_level(seed),
        "value_hypotheses": list(seed.business_targets),
        "prototype_targets": list(seed.prototype_targets),
        "checks": ["usefulness", "baseline", "review", "user need"],
    }
