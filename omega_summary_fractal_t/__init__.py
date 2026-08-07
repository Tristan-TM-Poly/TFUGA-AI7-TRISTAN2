"""Ω-SUMMARY-FRACTAL-T∞: deterministic multi-depth repository summarization."""

from .delta import delta_summaries, render_delta_markdown, write_delta
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
]

__version__ = "0.2.0"
