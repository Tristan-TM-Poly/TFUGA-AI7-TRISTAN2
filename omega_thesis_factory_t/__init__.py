"""Ω-THESIS-2N-GIT-T executable MVP.

This package converts a Tristan theory seed into a binary LOG/EXP PageTree,
OAK status metadata, and Git-ready planning artifacts.
"""

from .core import OAK_STATUS_ORDER, PageNode, ThesisSeed, build_page_tree, oak_report

__all__ = [
    "OAK_STATUS_ORDER",
    "PageNode",
    "ThesisSeed",
    "build_page_tree",
    "oak_report",
]
