from __future__ import annotations

from typing import Any, Mapping

from .core import Envelope, stable_digest

CUMULATIVE_INTELLIGENCE_BOUNDARY = (
    "historical_memory_and_reuse_context != semantic_truth_or_write_authority"
)


def adapt_cumulative_intelligence(report: Mapping[str, Any]) -> Envelope:
    """Map Ω-GITHUB-CUMULATIVE-INTELLIGENCE into the Research ABI knowledge graph."""
    body = dict(report)
    schema = str(body.get("schema") or "")
    if not schema.startswith("omega-github-cumulative-intelligence/"):
        raise TypeError("expected omega-github-cumulative-intelligence report")

    fingerprint = str(body.get("fingerprint") or stable_digest(body))
    refs = tuple(
        str(item.get("ref"))
        for item in body.get("relevant_pr_genomes", [])
        if isinstance(item, Mapping) and item.get("ref")
    )
    body["source_ontology"] = (
        "omega_capability_os_t.github_cumulative_intelligence.CumulativeIntelligenceCompiler"
    )
    body["bridge_boundary"] = CUMULATIVE_INTELLIGENCE_BOUNDARY

    return Envelope(
        graph="knowledge",
        object_type="github_cumulative_intelligence_context",
        object_id=fingerprint,
        payload=body,
        provenance=refs,
        authority="read",
        oak_state="UNKNOWN",
    )
