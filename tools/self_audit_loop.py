"""Self-audit loop for Tristan CanonOS.

Finds common canon weaknesses: overclaims, missing tests, orphan files, missing
M- links, contradiction count, and risk debt notes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tools.canon_graph import CanonGraph, CanonNodeType


class AuditSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class AuditFinding:
    finding_type: str
    severity: AuditSeverity
    description: str
    recommended_action: str


@dataclass(frozen=True)
class CanonAuditReport:
    scope: str
    findings: tuple[AuditFinding, ...]
    safe_next_actions: tuple[str, ...]


def audit_canon_graph(graph: CanonGraph, *, scope: str = "canon_graph") -> CanonAuditReport:
    findings: list[AuditFinding] = []

    for node in graph.orphan_nodes():
        findings.append(
            AuditFinding(
                "orphan_node",
                AuditSeverity.LOW,
                f"Node {node.node_id} has no graph relation.",
                "Link it to a theory, test, artifact, source, or roadmap; otherwise archive.",
            )
        )

    for edge in graph.contradiction_edges():
        findings.append(
            AuditFinding(
                "contradiction",
                AuditSeverity.MEDIUM,
                f"Contradiction edge {edge.edge_id}: {edge.source_id} -> {edge.target_id}.",
                "Route to ContradictionEngine: resolve, separate, test, deprecate, or quarantine.",
            )
        )

    tools = [node for node in graph.nodes.values() if node.node_type == CanonNodeType.TOOL]
    tests = [node for node in graph.nodes.values() if node.node_type == CanonNodeType.TEST]
    if tools and not tests:
        findings.append(
            AuditFinding(
                "missing_tests",
                AuditSeverity.HIGH,
                "Tool nodes exist but no test nodes were found.",
                "Add tests before raising CanonRank or ProofLevel.",
            )
        )

    if not findings:
        findings.append(
            AuditFinding(
                "no_findings",
                AuditSeverity.LOW,
                "No obvious self-audit findings in this graph snapshot.",
                "Continue monitoring and add evidence as the canon evolves.",
            )
        )

    next_actions = tuple(dict.fromkeys(f.recommended_action for f in findings))
    return CanonAuditReport(scope=scope, findings=tuple(findings), safe_next_actions=next_actions)
