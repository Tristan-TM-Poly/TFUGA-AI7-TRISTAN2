"""Ω-SUMMARY-FRACTAL-T∞: deterministic multi-depth repository summarization."""

from .aliases import approve_alias, identity_proposals, resolve_alias, verify_alias_registry
from .dashboard import build_dashboard, render_dashboard_markdown, write_dashboard
from .delta import delta_summaries, render_delta_markdown, write_delta
from .export import write_graph_exports, write_graphml, write_jsonl
from .fleet import (
    append_fleet_history,
    build_fleet_manifest,
    render_fleet_html,
    render_fleet_markdown,
    verify_fleet_history,
    write_fleet_manifest,
)
from .identity import content_signature, resolve_identity, write_identity_report
from .index import (
    append_snapshot,
    longitudinal_metrics,
    normalize_snapshot,
    verify_index,
    write_longitudinal_reports,
)
from .lineage import (
    build_system_lineage,
    convergence_candidates,
    proof_debt,
    superkernel_candidates,
)
from .models import EvidenceRef, SummaryBundle, SummaryNode
from .query import query_payload, render_query_markdown, write_query
from .query_plan import execute_query_plan, render_query_plan_markdown, write_query_plan
from .summarizer import SummaryEngine, build_summary

__all__ = [
    "EvidenceRef",
    "SummaryBundle",
    "SummaryNode",
    "SummaryEngine",
    "build_summary",
    "build_system_lineage",
    "convergence_candidates",
    "superkernel_candidates",
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
    "content_signature",
    "resolve_identity",
    "write_identity_report",
    "query_payload",
    "render_query_markdown",
    "write_query",
    "execute_query_plan",
    "render_query_plan_markdown",
    "write_query_plan",
    "build_dashboard",
    "render_dashboard_markdown",
    "write_dashboard",
    "build_fleet_manifest",
    "render_fleet_markdown",
    "render_fleet_html",
    "write_fleet_manifest",
    "append_fleet_history",
    "verify_fleet_history",
    "approve_alias",
    "identity_proposals",
    "resolve_alias",
    "verify_alias_registry",
]

__version__ = "0.5.0"
