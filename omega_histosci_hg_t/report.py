"""Deterministic audit and seed reports."""
from __future__ import annotations

from typing import Any

from .models import canonical_dict, content_hash
from .seed import build_seed


def build_report() -> dict[str, Any]:
    graph, registry = build_seed()
    graph_audit = graph.audit()
    registry_audit = registry.audit()
    report: dict[str, Any] = {
        "system": "Ω-HISTOSCI-HG-T∞",
        "version": "0.1.0",
        "status": "CERTIFIED_SOFTWARE_HISTORY_GRAPH_FIXTURES_R0_1",
        "graph": canonical_dict(graph_audit),
        "registry": canonical_dict(registry_audit),
        "macro_branch_count": len(registry.roots()),
        "branch_count": len(registry.branches),
        "source_count": len(registry.sources),
        "negative_memory_count": len(registry.negative_memories),
        "permanent_total_cap": None,
        "historical_truth_certified": False,
        "source_completeness_claimed": False,
        "global_exhaustiveness_claimed": False,
        "decolonial_completeness_claimed": False,
        "software_validation_only": True,
        "required_next_gate": "replace software fixtures with cited primary and secondary historical records",
    }
    report["digest"] = content_hash(report)
    return report
