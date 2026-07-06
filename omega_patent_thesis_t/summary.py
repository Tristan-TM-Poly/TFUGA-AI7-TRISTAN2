"""Short summary renderer."""

from __future__ import annotations

from .claim_tree import claim_tree
from .risk import risk_level
from .seed import PatentThesisSeed
from .value_map import value_map


def short_summary(seed: PatentThesisSeed) -> str:
    seed.validate()
    tree = claim_tree(seed)
    values = value_map(seed)
    lines = [
        f"# Technical Record Summary: {seed.title}",
        "",
        f"Record ID: `{seed.patent_id}`",
        f"Status: `{seed.status}`",
        f"Review level: `{risk_level(seed)}`",
        "",
        "## Problem",
        seed.core_problem or "Not specified.",
        "",
        "## Solution",
        seed.core_solution or "Not specified.",
        "",
        "## Claim counts",
        f"Independent: {len(tree['independent'])}",
        f"Dependent: {len(tree['dependent'])}",
        "",
        "## Prototype targets",
        ", ".join(values["prototype_targets"]) or "None listed.",
        "",
        "## Boundary",
        "This is a structured review scaffold, not external validation.",
    ]
    return "\n".join(lines) + "\n"
