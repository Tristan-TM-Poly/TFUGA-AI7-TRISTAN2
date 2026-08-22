"""Ω-THESIS-2N-GIT-T executable thesis factory.

This package converts a Tristan theory seed into a binary LOG/EXP PageTree,
OAK status metadata, Git-ready planning artifacts, and an exact 512-unit
research-monograph planning frontier built from depth 9 (512 = 2**9).
"""

from .core import OAK_STATUS_ORDER, PageNode, ThesisSeed, build_page_tree, oak_report
from .monograph512 import (
    DEFAULT_BUDGET,
    PAGE_TREE_DEPTH,
    TARGET_PAGES,
    SectionBudget,
    allocate_frontier,
    build_monograph_plan,
    frontier_512,
    validate_budget,
)

__all__ = [
    "OAK_STATUS_ORDER",
    "PageNode",
    "ThesisSeed",
    "build_page_tree",
    "oak_report",
    "DEFAULT_BUDGET",
    "PAGE_TREE_DEPTH",
    "TARGET_PAGES",
    "SectionBudget",
    "allocate_frontier",
    "build_monograph_plan",
    "frontier_512",
    "validate_budget",
]
