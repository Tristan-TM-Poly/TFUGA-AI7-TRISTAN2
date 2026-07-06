"""Theory-to-company map helpers for Tristan thesis seeds."""

from __future__ import annotations

from .core import ThesisSeed


def company_map(seed: ThesisSeed) -> dict:
    """Return a cautious product map from one seed.

    This is a hypothesis map, not proof of demand or revenue.
    """

    seed.validate()
    return {
        "seed_id": seed.id,
        "status": seed.status,
        "product_hypotheses": list(seed.venture_targets),
        "technical_assets": list(seed.code_targets),
        "repo_assets": list(seed.git_targets),
        "must_validate": [
            "user pain",
            "prototype usefulness",
            "baseline advantage",
            "maintenance cost",
            "risk controls",
        ],
        "blocked_claims": [
            "guaranteed revenue",
            "validated market",
            "production readiness",
        ],
    }
