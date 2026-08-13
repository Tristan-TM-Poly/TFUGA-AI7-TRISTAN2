"""Ω-THESIS-2N-GIT-T executable thesis factory.

The package converts Tristan theory seeds into binary LOG/EXP PageTrees and
adds a sparse order-n fractal thesis layer with ZOOM/DEZOOM review receipts.
"""

from .core import OAK_STATUS_ORDER, PageNode, ThesisSeed, build_page_tree, oak_report
from .forest import (
    DezoomReceipt,
    ThesisAddress,
    ThesisForest,
    ThesisNode,
    ZoomCandidate,
    ZoomPolicy,
    ZoomReceipt,
    dezoom_result,
    demo_zoom_candidates,
    root_thesis,
    thesis_forest_oak_report,
    zoom_thesis,
)

__all__ = [
    "OAK_STATUS_ORDER",
    "PageNode",
    "ThesisSeed",
    "build_page_tree",
    "oak_report",
    "ThesisAddress",
    "ThesisNode",
    "ThesisForest",
    "ZoomCandidate",
    "ZoomPolicy",
    "ZoomReceipt",
    "DezoomReceipt",
    "root_thesis",
    "zoom_thesis",
    "dezoom_result",
    "thesis_forest_oak_report",
    "demo_zoom_candidates",
]
