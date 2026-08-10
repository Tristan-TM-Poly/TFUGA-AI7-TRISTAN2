from __future__ import annotations

from typing import Any, Mapping, Sequence

from .graph import EpistemicGraphEngine
from .models import ProofDebtReport, SLOEvaluation, TruthSLO, TruthSLOReport


def _compare(value: float, operator: str, target: float) -> bool:
    if operator == ">=": return value >= target
    if operator == "<=": return value <= target
    if operator == "==": return value == target
    if operator == ">": return value > target
    if operator == "<": return value < target
    raise ValueError(operator)


class TruthSLOEngine:
    def metrics(self, engine: EpistemicGraphEngine, state: Mapping[str, Any], debt: ProofDebtReport) -> dict[str, float]:
        claims = [node for node in engine.graph.nodes if node.kind == "claim"]
        claim_state = state.get("claims", {})
        critical = [node for node in claims if node.criticality >= 4]
        current_critical = 0
        weighted_cov_num = 0.0
        weighted_cov_den = 0.0
        traceable = 0
        for node in claims:
            raw = claim_state.get(node.node_id, {}) if isinstance(claim_state, Mapping) else {}
            if not isinstance(raw, Mapping): raw = {}
            statuses = tuple(str(value) for value in raw.get("evidence_statuses", ()))
            if node in critical and statuses and all(value == "CURRENT" for value in statuses):
                current_critical += 1
            coverage = float(raw.get("coverage_score", 0.0))
            weighted_cov_num += coverage * node.criticality
            weighted_cov_den += node.criticality
            if bool(raw.get("provenance_complete", False)):
                traceable += 1
        residuals = [item for item in state.get("residuals", []) if isinstance(item, Mapping) and str(item.get("status", "OPEN")) in {"OPEN", "MITIGATED"}]
        conflicts = [item for item in state.get("conflicts", []) if isinstance(item, Mapping) and str(item.get("status", "OPEN")) == "OPEN"]
        return {
            "total_claims": float(len(claims)),
            "critical_claims_current_ratio": 1.0 if not critical else current_critical / len(critical),
            "weighted_claim_coverage": 0.0 if weighted_cov_den == 0 else weighted_cov_num / weighted_cov_den,
            "claim_traceability_ratio": 1.0 if not claims else traceable / len(claims),
            "open_critical_residuals": float(sum(str(item.get("severity", "")) == "critical" for item in residuals)),
            "open_evidence_conflicts": float(len(conflicts)),
            "proof_debt_score": float(debt.total_score),
            "critical_proof_debt_items": float(debt.critical_open),
        }

    def evaluate(self, engine: EpistemicGraphEngine, state: Mapping[str, Any], debt: ProofDebtReport, slos: Sequence[TruthSLO]) -> TruthSLOReport:
        metrics = self.metrics(engine, state, debt)
        evaluations: list[SLOEvaluation] = []
        for slo in sorted(slos, key=lambda item: item.slo_id):
            if slo.metric not in metrics:
                raise KeyError(f"unknown Truth SLO metric: {slo.metric}")
            observed = metrics[slo.metric]
            passed = _compare(observed, slo.operator, slo.target)
            evaluations.append(SLOEvaluation(
                slo_id=slo.slo_id,
                metric=slo.metric,
                observed=round(observed, 6),
                operator=slo.operator,
                target=slo.target,
                passed=passed,
                severity=slo.severity,
                reason=f"observed {observed:.6f} {slo.operator} target {slo.target:.6f}: {'pass' if passed else 'fail'}",
            ))
        critical_failures = sum(not item.passed and item.severity == "critical" for item in evaluations)
        return TruthSLOReport(
            evaluations=tuple(evaluations),
            metrics={key: round(value, 6) for key, value in metrics.items()},
            passed=critical_failures == 0,
            critical_failures=critical_failures,
            graph_id=engine.graph.graph_id,
        )


def slos_from_mapping(raw: Mapping[str, Any]) -> tuple[TruthSLO, ...]:
    return tuple(
        TruthSLO(
            slo_id=str(item["slo_id"]), metric=str(item["metric"]), operator=str(item["operator"]),
            target=float(item["target"]), severity=str(item["severity"]), description=str(item.get("description", "")),
        )
        for item in raw.get("slos", [])
    )
