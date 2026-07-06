"""Git path helper for patent thesis packs."""

from __future__ import annotations

from .seed import PatentThesisSeed


def gitpack_paths(seed: PatentThesisSeed) -> dict[str, list[str]]:
    seed.validate()
    base = seed.patent_id.lower().replace(" ", "_").replace("/", "_")
    return {
        "manifest": [f"patents/{base}/00_manifest/patent_seed.json"],
        "claims": [f"patents/{base}/01_claim_tree/claim_tree.json"],
        "thesis": [f"patents/{base}/02_thesis/thesis_short.md"],
        "prototype": [f"patents/{base}/03_prototype/prototype_plan.md"],
        "review": [f"patents/{base}/04_review/oak_review.md"],
    }
