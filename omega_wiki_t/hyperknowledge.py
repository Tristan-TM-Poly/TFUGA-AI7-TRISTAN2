"""R0.3 compiler for knowledge cells, contradictions, audits, and action queues."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Sequence

from .action_queue import ActionItem, build_action_queue, queue_summary
from .contradiction_engine import ClaimCollision, detect_claim_collisions
from .knowledge_cell import AuditReport, KnowledgeCell, audit_cells


class HyperKnowledgeCompiler:
    @staticmethod
    def compile(cells: Sequence[KnowledgeCell]) -> dict[str, Any]:
        audit = audit_cells(cells)
        collisions = detect_claim_collisions(cells)
        queue = build_action_queue(cells, audit.findings, collisions)
        return {
            "schema": "omega_hyperknowledge.bundle.v0.3",
            "cells": list(cells),
            "audit": audit,
            "collisions": collisions,
            "action_queue": queue,
            "manifest": {
                "cell_count": len(cells),
                "claim_count": sum(len(cell.claims) for cell in cells),
                "evidence_count": sum(len(cell.evidence) for cell in cells),
                "transition_count": sum(len(cell.transitions) for cell in cells),
                "collision_count": len(collisions),
                "action_count": len(queue),
                "queue_summary": queue_summary(queue),
                "oak_status": "R0.3_STRUCTURAL_EVIDENCE_GRAPH_NOT_SCIENTIFIC_CERTIFICATION",
            },
        }

    @staticmethod
    def write(bundle: dict[str, Any], output_dir: str | Path) -> Path:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        cells: list[KnowledgeCell] = bundle["cells"]
        audit: AuditReport = bundle["audit"]
        collisions: list[ClaimCollision] = bundle["collisions"]
        queue: list[ActionItem] = bundle["action_queue"]

        (output / "manifest.json").write_text(
            json.dumps(bundle["manifest"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "knowledge-cells.json").write_text(
            json.dumps([cell.to_dict() for cell in cells], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "audit.json").write_text(
            json.dumps(audit.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "claim-collisions.json").write_text(
            json.dumps([item.to_dict() for item in collisions], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "action-queue.json").write_text(
            json.dumps([item.to_dict() for item in queue], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with (output / "knowledge-cells.jsonl").open("w", encoding="utf-8") as stream:
            for cell in cells:
                stream.write(json.dumps(cell.to_dict(), ensure_ascii=False) + "\n")
        with (output / "action-queue.jsonl").open("w", encoding="utf-8") as stream:
            for item in queue:
                stream.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

        (output / "report.md").write_text(_render_report(bundle), encoding="utf-8")
        return output


def _render_report(bundle: dict[str, Any]) -> str:
    manifest = bundle["manifest"]
    audit: AuditReport = bundle["audit"]
    collisions: list[ClaimCollision] = bundle["collisions"]
    queue: list[ActionItem] = bundle["action_queue"]
    cells: list[KnowledgeCell] = bundle["cells"]

    lines = [
        "# Ω-HYPERKNOWLEDGE-T∞ R0.3 report",
        "",
        f"- Cells: **{manifest['cell_count']}**",
        f"- Claims: **{manifest['claim_count']}**",
        f"- Evidence records: **{manifest['evidence_count']}**",
        f"- OAK transitions: **{manifest['transition_count']}**",
        f"- Claim collisions: **{manifest['collision_count']}**",
        f"- Actions: **{manifest['action_count']}**",
        f"- OAK status: `{manifest['oak_status']}`",
        "",
        "## Coverage metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in audit.metrics.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Action queue", "", "| Priority | Cell | Category | Action |", "|---|---|---|---|"])
    for item in queue:
        lines.append(f"| {item.priority} | {item.cell_id} | {item.category} | {item.action} |")

    lines.extend(["", "## Claim collisions", ""])
    if not collisions:
        lines.append("No contradiction or duplicate candidates detected.")
    for collision in collisions:
        lines.append(
            f"- **{collision.kind}** `{collision.canonical_key}` — claims "
            f"{', '.join(collision.claim_ids)}; status: `{collision.status}`."
        )

    lines.extend(["", "## Knowledge cells", ""])
    for cell in cells:
        lines.extend(
            [
                f"### {cell.subject}",
                "",
                f"- Cell: `{cell.cell_id}`",
                f"- Domain: `{cell.domain}`",
                f"- OAK status: `{cell.oak_status}`",
                f"- Claims: {len(cell.claims)}",
                f"- Evidence: {len(cell.evidence)}",
                f"- Next actions: {len(cell.next_actions)}",
                "",
            ]
        )

    lines.extend(
        [
            "## OAK boundary",
            "",
            "This bundle checks structure, provenance, evidence linkage, contradictions, and promotion residues. "
            "It does not prove claims, certify physics, establish patentability, or guarantee product value.",
            "",
        ]
    )
    return "\n".join(lines)
