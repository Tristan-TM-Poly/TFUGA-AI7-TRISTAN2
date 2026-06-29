"""JSON IO helpers for reusable Daily Omega signals.

The IO layer converts portable JSON dictionaries into BriefingItem objects and
exports reviewable outputs. It performs no network calls and creates no GitHub
issues, so it is safe for local scripts, CI, and dry-run agents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_router import make_issue_spec, route_item
from sage_tristan.daily_omega_supervisor import supervise_issue_spec


def source_from_dict(data: Mapping[str, Any]) -> Source:
    """Create a Source from a JSON-like dictionary."""

    return Source(
        title=str(data["title"]),
        source_type=str(data.get("source_type", "other")),
        url_or_identifier=str(data["url_or_identifier"]),
        source_quality=int(data.get("source_quality", 3)),
    )


def oak_from_dict(data: Mapping[str, Any]) -> OakCheck:
    """Create an OakCheck from a JSON-like dictionary."""

    return OakCheck(
        claim_status=str(data.get("claim_status", "prototype_opportunity")),
        risk=str(data["risk"]),
        falsification_route=str(data["falsification_route"]),
        limit=str(data.get("limit", "")),
        uncertainty=str(data.get("uncertainty", "")),
        m_minus_warning=str(data.get("m_minus_warning", "")),
    )


def item_from_dict(data: Mapping[str, Any]) -> BriefingItem:
    """Create a BriefingItem from a portable signal dictionary."""

    sources = tuple(source_from_dict(source) for source in data.get("sources", []))
    if not sources:
        raise ValueError("Daily Omega signal requires at least one source")

    return BriefingItem(
        title=str(data["title"]),
        topic_anchor=str(data["topic_anchor"]),
        signal_type=tuple(str(value) for value in data.get("signal_type", ["opportunity"])),
        why_it_matters=str(data["why_it_matters"]),
        actionable_opportunity=str(data["actionable_opportunity"]),
        oak_check=oak_from_dict(data["oak_check"]),
        sources=sources,
        next_action=str(data["next_action"]),
        scores={str(key): int(value) for key, value in dict(data.get("scores", {})).items()},
        business_funding_signal=str(data.get("business_funding_signal", "")),
        ip_signal=str(data.get("ip_signal", "")),
        rank=int(data["rank"]) if "rank" in data else None,
    )


def load_item_json(path: str | Path) -> BriefingItem:
    """Load one Daily Omega signal JSON file."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Daily Omega JSON root must be an object")
    return item_from_dict(payload)


def export_decision_dict(item: BriefingItem, *, dry_run: bool = True) -> dict[str, Any]:
    """Export the reusable supervision result as plain JSON-safe data."""

    route = route_item(item)
    issue = make_issue_spec(item)
    decision = supervise_issue_spec(item, dry_run=dry_run)
    return {
        "title": item.title,
        "final_score": item.final_score,
        "canon_branches": list(route.branches),
        "ip_classification": route.ip_classification,
        "issue_type": route.issue_type,
        "supervision": {
            "allowed": decision.allowed,
            "mode": decision.mode,
            "reasons": list(decision.reasons),
        },
        "issue_spec": {
            "title": issue.title,
            "labels": list(issue.labels),
            "body": issue.body,
        },
    }


def export_decision_json(item: BriefingItem, *, dry_run: bool = True, indent: int = 2) -> str:
    """Return a JSON string for one supervised Daily Omega signal."""

    return json.dumps(export_decision_dict(item, dry_run=dry_run), indent=indent, ensure_ascii=False)


def export_decision_markdown(item: BriefingItem, *, dry_run: bool = True) -> str:
    """Return Markdown for one supervised Daily Omega signal."""

    decision = supervise_issue_spec(item, dry_run=dry_run)
    return decision.render_markdown() + "\n" + decision.issue_spec.body


__all__ = [
    "export_decision_dict",
    "export_decision_json",
    "export_decision_markdown",
    "item_from_dict",
    "load_item_json",
    "oak_from_dict",
    "source_from_dict",
]
