"""Route confidence dashboard for Omega absorb v1.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .adapter_router import AdapterRoute, detect_source_family


@dataclass(frozen=True)
class RouteConfidenceRow:
    index: int
    source_id: str
    adapter_name: str
    confidence: float
    reasons: Tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class RouteConfidenceDashboard:
    rows: Tuple[RouteConfidenceRow, ...]
    average_confidence: float
    next_action: str


def build_route_confidence_dashboard(records: Iterable[dict]) -> RouteConfidenceDashboard:
    rows = []
    for index, record in enumerate(records, start=1):
        route: AdapterRoute = detect_source_family(record)
        rows.append(
            RouteConfidenceRow(
                index=index,
                source_id=route.source_id,
                adapter_name=route.adapter_name,
                confidence=route.confidence,
                reasons=route.reasons,
                next_action=route.next_action,
            )
        )
    avg = round(sum(row.confidence for row in rows) / len(rows), 4) if rows else 0.0
    return RouteConfidenceDashboard(tuple(rows), avg, "route_low_confidence_records")


def render_route_confidence_dashboard(dashboard: RouteConfidenceDashboard) -> str:
    lines = ["index | source | adapter | confidence | reasons", "--- | --- | --- | --- | ---"]
    for row in dashboard.rows:
        lines.append(f"{row.index} | {row.source_id} | {row.adapter_name} | {row.confidence:.4f} | {', '.join(row.reasons)}")
    lines.append(f"average | all | all | {dashboard.average_confidence:.4f} | summary")
    return "\n".join(lines) + "\n"
