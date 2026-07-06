"""DebtBurner engine for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Visible debt becomes a traceable, reversible task. Planning only; this module
never performs external effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DebtType(StrEnum):
    PROOF = "proof_debt"
    RISK = "risk_debt"
    TEST = "test_debt"
    BENCHMARK = "benchmark_debt"
    SOURCE = "source_debt"
    ROLLBACK = "rollback_debt"
    PRIVACY = "privacy_debt"
    IP = "ip_debt"
    DOCUMENTATION = "documentation_debt"
    CANON_LINK = "canon_link_debt"


@dataclass(frozen=True)
class DebtPacket:
    debt_type: DebtType
    context: str
    severity: int = 1
    evidence: str = "visible_gap"


@dataclass(frozen=True)
class DebtTask:
    task_type: str
    queue: str
    artifact: str
    context: str
    status: str = "ready_for_queue"


DEBT_RESOLUTION_MAP: dict[DebtType, tuple[str, str, str]] = {
    DebtType.PROOF: ("generate_test_or_benchmark", "Q3", "tests/"),
    DebtType.RISK: ("generate_oak_report", "Q5", "docs/oak_reports/"),
    DebtType.TEST: ("generate_test_skeleton", "Q3", "tests/"),
    DebtType.BENCHMARK: ("generate_benchmark_skeleton", "Q4", "benchmarks/"),
    DebtType.SOURCE: ("generate_source_status_note", "Q5", "docs/source_notes/"),
    DebtType.ROLLBACK: ("generate_rollback_plan", "Q5", "docs/rollback_plans/"),
    DebtType.PRIVACY: ("generate_privacy_review_note", "Q10", "docs/review_packets/"),
    DebtType.IP: ("generate_ip_classification_note", "Q10", "docs/ip/"),
    DebtType.DOCUMENTATION: ("generate_documentation_patch", "Q5", "docs/"),
    DebtType.CANON_LINK: ("generate_canon_graph_edge", "Q9", "configs/canon_graph/"),
}


def normalize_debt_type(debt_type: DebtType | str) -> DebtType:
    if isinstance(debt_type, DebtType):
        return debt_type
    try:
        return DebtType(debt_type)
    except ValueError as exc:
        raise ValueError(f"unknown debt type: {debt_type}") from exc


def convert_debt_to_task(debt_type: DebtType | str, context: str, *, severity: int = 1) -> DebtTask:
    """Convert visible debt into the next reversible artifact-producing task."""
    normalized = normalize_debt_type(debt_type)
    task_type, queue, artifact = DEBT_RESOLUTION_MAP[normalized]
    if severity >= 8 and queue not in {"Q10", "Q5"}:
        queue = "Q10"
    return DebtTask(task_type=task_type, queue=queue, artifact=artifact, context=context)


def burn_debt_packets(packets: tuple[DebtPacket, ...]) -> tuple[DebtTask, ...]:
    return tuple(convert_debt_to_task(packet.debt_type, packet.context, severity=packet.severity) for packet in packets)
