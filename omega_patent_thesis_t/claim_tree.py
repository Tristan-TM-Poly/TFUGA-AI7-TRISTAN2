"""Claim tree helper."""

from __future__ import annotations

from .seed import PatentThesisSeed


def claim_tree(seed: PatentThesisSeed) -> dict:
    seed.validate()
    return {
        "patent_id": seed.patent_id,
        "root": seed.title,
        "independent": [
            {"id": f"I{i + 1}", "summary": claim}
            for i, claim in enumerate(seed.independent_claims)
        ],
        "dependent": [
            {"id": f"D{i + 1}", "summary": claim}
            for i, claim in enumerate(seed.dependent_claims)
        ],
    }
