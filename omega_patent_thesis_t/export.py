"""Export helper."""

from __future__ import annotations

from .claim_tree import claim_tree
from .gitpack import gitpack_paths
from .review import review_card
from .seed import PatentThesisSeed
from .summary import short_summary
from .value_map import value_map


def export_pack(seed: PatentThesisSeed) -> dict:
    seed.validate()
    return {
        "seed": seed.to_dict(),
        "claim_tree": claim_tree(seed),
        "review": review_card(seed),
        "value_map": value_map(seed),
        "gitpack": gitpack_paths(seed),
        "summary": short_summary(seed),
    }
