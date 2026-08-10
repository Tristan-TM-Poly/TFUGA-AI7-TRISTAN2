from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from .graph import EpistemicGraphEngine
from .models import ProofDebtItem, ProofDebtReport, stable_digest

_BASE = {"low": 1.0, "medium": 3.0, "high": 8.0, "critical": 13.0}


class ProofDebtEngine:
    def evaluate(self, engine: EpistemicGraphEngine, state: Mapping[str, Any]) -> ProofDebtReport:
        items: list[ProofDebtItem] = []
        claim_state = state.get("claims", {})
        if not isinstance(claim_state, Mapping):
            raise TypeError("state.claims must be an object")
        evidence_edges = defaultdict(list)
        test_edges = defaultdict(list)
        for edge in engine.graph.edges:
            if edge.relation in {"supported_by", "contradicted_by"}:
                evidence_edges[edge.source].append(edge.target)
            if edge.relation == "verified_by":
                test_edges[edge.source].append(edge.target)

        for node in sorted(engine.graph.nodes, key=lambda item: item.node_id):
            if node.kind != "claim":
                continue
            raw = claim_state.get(node.node_id, {})
            if not isinstance(raw, Mapping):
                raw = {}
            criticality = node.criticality
            default_severity = "critical" if criticality >= 5 else "high" if criticality >= 4 else "medium" if criticality >= 2 else "low"
            if not evidence_edges[node.node_id]:
                items.append(self._item("missing_evidence", default_severity, (node.node_id,), criticality, "claim has no supporting or contradicting evidence edge", ("add_provenanced_evidence",)))
            coverage = float(raw.get("coverage_score", 0.0))
            threshold = float(raw.get("coverage_threshold", 0.8))
            if coverage < threshold:
                items.append(self._item("low_claim_coverage", default_severity, (node.node_id,), criticality, f"claim coverage {coverage:.3f} is below {threshold:.3f}", ("add_required_evidence_kinds", "restore_claim_to_test_provenance")))
            required_tests = int(raw.get("required_tests", len(test_edges[node.node_id])))
            observed_tests = int(raw.get("observed_tests", 0))
            if observed_tests < required_tests:
                items.append(self._item("missing_tests", default_severity, (node.node_id,), criticality, f"observed {observed_tests} of {required_tests} required tests", ("run_or_generate_missing_tests",)))
            statuses = tuple(str(value) for value in raw.get("evidence_statuses", ()))
            noncurrent = tuple(sorted(status for status in statuses if status != "CURRENT"))
            if noncurrent:
                severity = "critical" if "INVALIDATED" in noncurrent or "REVOKED" in noncurrent else default_severity
                items.append(self._item("noncurrent_evidence", severity, (node.node_id,), criticality, f"non-current evidence states: {', '.join(noncurrent)}", ("refresh_evidence", "recompute_validity")))
            if not bool(raw.get("provenance_complete", False)):
                items.append(self._item("missing_provenance", default_severity, (node.node_id,), criticality, "claim evidence provenance is incomplete", ("restore_claim_test_evidence_links",)))

        for residual in state.get("residuals", []):
            if not isinstance(residual, Mapping) or str(residual.get("status", "OPEN")) not in {"OPEN", "MITIGATED"}:
                continue
            severity = str(residual.get("severity", "medium"))
            node_ids = tuple(sorted(str(value) for value in residual.get("claim_ids", ())))
            items.append(self._item("open_residual", severity, node_ids, 1, str(residual.get("summary", residual.get("id", "open residual"))), ("resolve_accept_or_transfer_residual",)))

        for conflict in state.get("conflicts", []):
            if not isinstance(conflict, Mapping) or str(conflict.get("status", "OPEN")) != "OPEN":
                continue
            claim_id = str(conflict.get("claim_id", ""))
            severity = str(conflict.get("severity", "medium"))
            items.append(self._item("evidence_conflict", severity, (claim_id,) if claim_id else (), 1, "supporting and contradicting evidence remain unresolved", ("run_discriminating_experiment", "narrow_claim_scope")))

        items = sorted(items, key=lambda item: (-item.score, item.category, item.debt_id))
        severity_counts = {key: 0 for key in _BASE}
        category_counts: dict[str, int] = defaultdict(int)
        for item in items:
            severity_counts[item.severity] += 1
            category_counts[item.category] += 1
        return ProofDebtReport(
            items=tuple(items),
            total_score=round(sum(item.score for item in items), 6),
            counts_by_severity=severity_counts,
            counts_by_category=dict(sorted(category_counts.items())),
            critical_open=severity_counts["critical"],
            graph_id=engine.graph.graph_id,
        )

    def _item(self, category: str, severity: str, node_ids: tuple[str, ...], criticality: int, reason: str, remediation: tuple[str, ...]) -> ProofDebtItem:
        score = _BASE.get(severity, _BASE["medium"]) * max(1.0, criticality / 2.0)
        identity = {"category": category, "severity": severity, "node_ids": list(node_ids), "reason": reason}
        return ProofDebtItem(
            debt_id=f"PDEBT-{stable_digest(identity)[:16].upper()}",
            category=category,
            severity=severity,
            node_ids=node_ids,
            score=round(score, 6),
            reason=reason,
            remediation=remediation,
        )
