"""Batch reports for canonical thesis seeds."""

from __future__ import annotations

from .company_map import company_map
from .pack import make_pack
from .seed_registry import canonical_seeds


def batch_report(depth: int = 2) -> dict:
    items = {}
    for seed_id, seed in canonical_seeds().items():
        pack = make_pack(seed, depth=depth)
        items[seed_id] = {
            "status": seed.status,
            "frontier_pages": pack["report"]["frontier_pages"],
            "total_nodes": pack["report"]["total_nodes"],
            "products": company_map(seed)["product_hypotheses"],
        }
    return {"count": len(items), "depth": depth, "items": items}


def portfolio_summary(depth: int = 2) -> dict:
    report = batch_report(depth=depth)
    total_nodes = sum(item["total_nodes"] for item in report["items"].values())
    total_pages = sum(item["frontier_pages"] for item in report["items"].values())
    return {
        "seed_count": report["count"],
        "depth": depth,
        "total_nodes": total_nodes,
        "frontier_pages": total_pages,
    }
