"""Ω-SUMMARY-FRACTAL-T∞: deterministic multi-depth repository summarization."""

from .models import EvidenceRef, SummaryBundle, SummaryNode
from .summarizer import SummaryEngine, build_summary

__all__ = [
    "EvidenceRef",
    "SummaryBundle",
    "SummaryNode",
    "SummaryEngine",
    "build_summary",
]

__version__ = "0.1.0"
