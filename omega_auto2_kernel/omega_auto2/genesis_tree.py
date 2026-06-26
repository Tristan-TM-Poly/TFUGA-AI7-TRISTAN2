from __future__ import annotations


def build_genesis_tree(intent: str) -> dict[str, object]:
    clean = intent.strip() or "AUTO-GENESIS"
    return {
        "root": clean,
        "trunk": "intention_to_verified_artifact",
        "branches": [
            "workflow",
            "prototype",
            "oak_validation",
            "github_plan",
            "revenue_ip_paths",
            "m_plus_m_minus",
        ],
        "leaves": ["tasks", "tests", "docs", "reports", "fixtures"],
        "fruits": ["prototype", "proof", "asset", "offer", "publication_candidate"],
        "seeds": ["next_pr", "next_benchmark", "next_product", "next_oak_check"],
    }
