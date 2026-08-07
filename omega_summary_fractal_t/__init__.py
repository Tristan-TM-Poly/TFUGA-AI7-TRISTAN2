"""Ω-SUMMARY-FRACTAL-T∞: deterministic multi-depth repository summarization."""

from .delta import delta_summaries, render_delta_markdown, write_delta
from .export import write_graph_exports, write_graphml, write_jsonl
from .index import (
    append_snapshot,
    longitudinal_metrics,
    normalize_snapshot,
    verify_index,
    write_longitudinal_reports,
)
from .lineage import build_system_lineage, convergence_candidates, proof_debt
from .models import EvidenceRef, SummaryBundle, SummaryNode
from .summarizer import SummaryEngine, build_summary

__all__ = [
    "EvidenceRef",
    "SummaryBundle",
    "SummaryNode",
    "SummaryEngine",
    "build_summary",
    "build_system_lineage",
    "convergence_candidates",
    "proof_debt",
    "delta_summaries",
    "render_delta_markdown",
    "write_delta",
    "append_snapshot",
    "longitudinal_metrics",
    "normalize_snapshot",
    "verify_index",
    "write_longitudinal_reports",
    "write_graph_exports",
    "write_graphml",
    "write_jsonl",
]

__version__ = "0.3.0"
