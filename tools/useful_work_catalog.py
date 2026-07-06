"""Useful Work Catalog for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Returns reversible repo work options for safe continuation.
"""

from __future__ import annotations


CATALOG = (
    "create_index",
    "add_tests",
    "write_docs",
    "link_canon_graph",
    "create_learning_note",
    "write_oak_report",
    "prepare_review_packet",
    "add_examples",
    "improve_readme",
    "add_benchmark_skeleton",
)


def list_work_options(limit: int = 5) -> tuple[str, ...]:
    return CATALOG[: max(0, min(limit, len(CATALOG)))]
