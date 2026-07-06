"""Review-risk helper for patent thesis seeds."""

from __future__ import annotations

from .seed import PatentThesisSeed


def risk_level(seed: PatentThesisSeed) -> str:
    seed.validate()
    risk_text = " ".join(seed.oak_risks).lower()
    status = seed.status.lower()
    if "requires expert review" in risk_text:
        return "review"
    if status in {"unknown", "pending"}:
        return "review"
    if status in {"expired", "abandoned"}:
        return "low"
    if status == "granted":
        return "high"
    return "review"
