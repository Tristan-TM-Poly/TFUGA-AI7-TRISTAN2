"""Small review helper."""

from __future__ import annotations

from .risk import risk_level
from .seed import PatentThesisSeed


def review_card(seed: PatentThesisSeed) -> dict:
    seed.validate()
    return {
        "record_id": seed.patent_id,
        "status": seed.status,
        "level": risk_level(seed),
        "checks": [
            "claim summary",
            "prototype target",
            "baseline question",
            "expert review",
        ],
        "boundary": "structured review only",
    }
