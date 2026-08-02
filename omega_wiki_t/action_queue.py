"""Prioritized action queue for Ω-HYPERKNOWLEDGE-T∞ R0.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .contradiction_engine import ClaimCollision
from .knowledge_cell import AuditFinding, KnowledgeCell, stable_id


PRIORITY_ORDER = {f"P{index}": index for index in range(7)}


@dataclass(frozen=True)
class ActionItem:
    action_id: str
    priority: str
    cell_id: str
    category: str
    action: str
    reason: str
    claim_id: str | None = None
    blockers: tuple[str, ...] = ()
    approval_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_action_queue(
    cells: Sequence[KnowledgeCell],
    findings: Sequence[AuditFinding],
    collisions: Sequence[ClaimCollision],
) -> list[ActionItem]:
    queue: list[ActionItem] = []
    cells_by_id = {cell.cell_id: cell for cell in cells}

    for finding in findings:
        action = finding.suggested_action or "Review and resolve the finding."
        queue.append(
            ActionItem(
                action_id=stable_id("action", finding.finding_id, action),
                priority=finding.severity,
                cell_id=finding.cell_id,
                category=finding.category,
                action=action,
                reason=finding.message,
                claim_id=finding.claim_id,
                blockers=(finding.finding_id,),
                approval_required=finding.category in {"ip_disclosure_risk", "physics_without_measurement"},
            )
        )

    for collision in collisions:
        priority = "P0" if collision.kind == "potential_contradiction" else "P5"
        for cell_id in collision.cell_ids:
            queue.append(
                ActionItem(
                    action_id=stable_id("action", collision.collision_id, cell_id),
                    priority=priority,
                    cell_id=cell_id,
                    category=collision.kind,
                    action=(
                        "Compare protocols, scopes, datasets, metrics, timestamps, and assumptions; then mark "
                        "the claims as contradiction, context-dependent, duplicate, or not equivalent."
                    ),
                    reason=collision.explanation,
                    blockers=(collision.collision_id,),
                )
            )

    for cell in cells:
        if cell.oak_status == "ARCHIVED":
            queue.append(
                ActionItem(
                    action_id=stable_id("action", cell.cell_id, "archive"),
                    priority="P6",
                    cell_id=cell.cell_id,
                    category="archive",
                    action="Keep historical provenance and exclude from active promotion queues.",
                    reason="Knowledge cell is archived.",
                )
            )
        elif not any(item.cell_id == cell.cell_id for item in queue):
            queue.append(
                ActionItem(
                    action_id=stable_id("action", cell.cell_id, "enrichment"),
                    priority="P3",
                    cell_id=cell.cell_id,
                    category="external_enrichment",
                    action="Enrich with independent sources, identifiers, prior art, standards, and counterexamples.",
                    reason="Cell passed structural audit but still benefits from independent evidence enrichment.",
                )
            )

    unique = {item.action_id: item for item in queue}
    return sorted(
        unique.values(),
        key=lambda item: (
            PRIORITY_ORDER.get(item.priority, 99),
            item.cell_id,
            item.category,
            item.action_id,
        ),
    )


def queue_summary(queue: Sequence[ActionItem]) -> dict[str, int]:
    summary = {f"P{index}": 0 for index in range(7)}
    for item in queue:
        summary[item.priority] = summary.get(item.priority, 0) + 1
    return summary
