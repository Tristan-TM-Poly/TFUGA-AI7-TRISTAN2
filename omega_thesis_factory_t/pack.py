"""Small pack helper for thesis seeds."""

from __future__ import annotations

from .core import ThesisSeed, build_page_tree, oak_report


def make_pack(seed: ThesisSeed, depth: int = 2) -> dict:
    seed.validate()
    nodes = build_page_tree(seed, depth)
    return {
        "seed": seed.to_dict(),
        "depth": depth,
        "nodes": [node.to_dict() for node in nodes],
        "report": oak_report(seed, nodes),
    }
