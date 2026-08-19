"""Organ Splitter for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Plans safe package organs for a large draft PR. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrganPlan:
    organ_id: str
    title: str
    required_parts: tuple[str, ...]


def default_pr220_organs() -> tuple[OrganPlan, ...]:
    parts = ("README", "tools", "tests", "schemas", "safety", "oak_report", "imports", "owner_note")
    names = (
        "biotox_safety",
        "ait_bio_oak",
        "immunome",
        "worldmodel_hallucination",
        "reality_forge",
        "canon_os",
        "research_factory",
        "no_human_bottleneck",
        "continuation_engine",
        "propulsion_mesh",
        "shared_schemas",
        "shared_oak_safety",
    )
    return tuple(OrganPlan(f"organ_{idx:02d}", name, parts) for idx, name in enumerate(names, start=1))
