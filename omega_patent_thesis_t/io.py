"""JSON loading helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .seed import PatentThesisSeed


def seed_from_dict(data: dict) -> PatentThesisSeed:
    return PatentThesisSeed(
        patent_id=data["patent_id"],
        title=data["title"],
        status=data.get("status", "unknown"),
        domains=tuple(data.get("domains", ())),
        core_problem=data.get("core_problem", ""),
        core_solution=data.get("core_solution", ""),
        independent_claims=tuple(data.get("independent_claims", ())),
        dependent_claims=tuple(data.get("dependent_claims", ())),
        prototype_targets=tuple(data.get("prototype_targets", ())),
        business_targets=tuple(data.get("business_targets", ())),
        oak_risks=tuple(data.get("oak_risks", ())),
    )


def load_seed(path: str | Path) -> PatentThesisSeed:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    seed = seed_from_dict(data)
    seed.validate()
    return seed
