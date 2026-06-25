"""Daily Omega Intelligence OS compiler.

This layer converts a BriefingItem into a reusable SignalGenome: a compact,
JSON-safe strategic object that connects OAK review, canon routing, IP posture,
prototype horizon, revenue path, memory notes, and canon status.

It performs no network calls and creates no public issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from sage_tristan.daily_omega_briefing import BriefingItem
from sage_tristan.daily_omega_router import route_item
from sage_tristan.daily_omega_supervisor import supervise_issue_spec

PROTOTYPE_HORIZONS = ("none", "15_min", "2_hour", "1_day", "1_week")
REVENUE_ROUTES = (
    "none",
    "service",
    "audit",
    "report",
    "template",
    "software",
    "dataset",
    "api",
    "grant",
    "consulting",
    "licensing",
    "course",
)


@dataclass(frozen=True)
class SignalGenome:
    """Portable strategic genome for one Daily Omega signal."""

    title: str
    final_score: int
    canon_branches: tuple[str, ...]
    ip_classification: str
    issue_type: str
    supervision_mode: str
    prototype_horizon: str
    revenue_routes: tuple[str, ...]
    canon_status: str
    m_plus: str
    m_minus: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "final_score": self.final_score,
            "canon_branches": list(self.canon_branches),
            "ip_classification": self.ip_classification,
            "issue_type": self.issue_type,
            "supervision_mode": self.supervision_mode,
            "prototype_horizon": self.prototype_horizon,
            "revenue_routes": list(self.revenue_routes),
            "canon_status": self.canon_status,
            "m_plus": self.m_plus,
            "m_minus": self.m_minus,
            "next_action": self.next_action,
        }


def infer_prototype_horizon(item: BriefingItem) -> str:
    """Infer the smallest useful prototype horizon for an item."""

    text = " ".join(
        [
            item.title,
            item.actionable_opportunity,
            item.next_action,
            " ".join(item.signal_type),
        ]
    ).lower()

    if "verify" in text or "source" in text:
        return "15_min"
    if "matrix" in text or "tracker" in text or "benchmark" in text:
        return "2_hour"
    if "prototype" in text or "pipeline" in text or "dataset" in text:
        return "1_day"
    if item.final_score >= 28:
        return "1_week"
    return "none"


def infer_revenue_routes(item: BriefingItem) -> tuple[str, ...]:
    """Infer plausible, testable revenue routes from item text."""

    text = " ".join(
        [
            item.title,
            item.business_funding_signal,
            item.actionable_opportunity,
            item.next_action,
            " ".join(item.signal_type),
        ]
    ).lower()
    routes: list[str] = []

    keyword_routes = {
        "service": "service",
        "audit": "audit",
        "report": "report",
        "template": "template",
        "software": "software",
        "dataset": "dataset",
        "api": "api",
        "grant": "grant",
        "subvention": "grant",
        "consult": "consulting",
        "licensing": "licensing",
        "licence": "licensing",
        "course": "course",
        "veille": "report",
        "prior-art": "service",
        "benchmark": "audit",
    }
    for keyword, route in keyword_routes.items():
        if keyword in text and route not in routes:
            routes.append(route)

    if not routes and item.final_score >= 20:
        routes.append("service")
    return tuple(routes or ["none"])


def infer_canon_status(item: BriefingItem) -> str:
    """Infer conservative canon status from sources and OAK state."""

    if not item.sources:
        return "raw_signal"
    if any(source.source_quality <= 1 for source in item.sources):
        return "source_required"
    if item.oak_check.claim_status in {"validated", "measured_result", "validated_result"}:
        return "validated"
    if item.final_score >= 26 and item.oak_check.falsification_route:
        return "prototype_candidate"
    if item.final_score >= 18:
        return "issue_candidate"
    return "imported_signal"


def compile_signal_genome(item: BriefingItem, *, dry_run: bool = True) -> SignalGenome:
    """Compile one item into a reusable SignalGenome."""

    route = route_item(item)
    decision = supervise_issue_spec(item, dry_run=dry_run)
    return SignalGenome(
        title=item.title,
        final_score=item.final_score,
        canon_branches=route.branches,
        ip_classification=route.ip_classification,
        issue_type=route.issue_type,
        supervision_mode=decision.mode,
        prototype_horizon=infer_prototype_horizon(item),
        revenue_routes=infer_revenue_routes(item),
        canon_status=infer_canon_status(item),
        m_plus=route.m_plus,
        m_minus=route.m_minus,
        next_action=item.next_action,
    )


def compile_many(items: Iterable[BriefingItem], *, dry_run: bool = True) -> list[SignalGenome]:
    """Compile many Daily Omega items into SignalGenomes."""

    return [compile_signal_genome(item, dry_run=dry_run) for item in items]


def render_intelligence_os_markdown(genomes: Iterable[SignalGenome]) -> str:
    """Render a compact Intelligence OS report section."""

    lines = ["# Daily Ω Intelligence OS", ""]
    for index, genome in enumerate(genomes, start=1):
        lines.extend(
            [
                f"## {index}. {genome.title}",
                f"- **Score:** {genome.final_score}",
                f"- **Canon status:** {genome.canon_status}",
                f"- **Branches:** {', '.join(genome.canon_branches) or 'Unrouted'}",
                f"- **IP:** {genome.ip_classification}",
                f"- **Issue type:** {genome.issue_type}",
                f"- **Supervisor:** {genome.supervision_mode}",
                f"- **Prototype horizon:** {genome.prototype_horizon}",
                f"- **Revenue routes:** {', '.join(genome.revenue_routes)}",
                f"- **M-:** {genome.m_minus}",
                f"- **Next action:** {genome.next_action}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


__all__ = [
    "PROTOTYPE_HORIZONS",
    "REVENUE_ROUTES",
    "SignalGenome",
    "compile_many",
    "compile_signal_genome",
    "infer_canon_status",
    "infer_prototype_horizon",
    "infer_revenue_routes",
    "render_intelligence_os_markdown",
]
