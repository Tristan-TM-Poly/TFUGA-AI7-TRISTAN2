from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Sequence

from .models import FaultMode, SystemBlueprint


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class FaultPropagationRecord:
    fault: FaultMode
    affected_components: tuple[str, ...]
    affected_domains: tuple[str, ...]
    propagation_depth: int
    critical_components_reached: tuple[str, ...]
    single_point_risk: bool
    mitigation_priority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault": self.fault.to_dict(),
            "affected_components": list(self.affected_components),
            "affected_domains": list(self.affected_domains),
            "propagation_depth": self.propagation_depth,
            "critical_components_reached": list(self.critical_components_reached),
            "single_point_risk": self.single_point_risk,
            "mitigation_priority": self.mitigation_priority,
        }


@dataclass(frozen=True)
class FaultPropagationReport:
    system_id: str
    records: tuple[FaultPropagationRecord, ...]
    highest_rpn: int
    single_point_risk_count: int
    critical_path_count: int
    heuristic_resilience_score: float
    evidence_hash: str
    probability_claim: bool = False
    safety_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "records": [item.to_dict() for item in self.records],
            "highest_rpn": self.highest_rpn,
            "single_point_risk_count": self.single_point_risk_count,
            "critical_path_count": self.critical_path_count,
            "heuristic_resilience_score": self.heuristic_resilience_score,
            "evidence_hash": self.evidence_hash,
            "probability_claim": self.probability_claim,
            "safety_certified": self.safety_certified,
            "limitations": [
                "propagation follows declared directed interfaces only",
                "RPN is an ordinal prioritization heuristic, not a failure probability",
                "common-cause, latent, human and environmental faults require separate analysis",
                "functional-safety certification requires qualified external processes",
            ],
        }


def _mitigation_priority(fault: FaultMode, critical_count: int, single_point: bool) -> str:
    rpn = fault.risk_priority_number
    if fault.severity >= 9 or single_point or critical_count >= 2 or rpn >= 200:
        return "immediate_design_review"
    if fault.severity >= 7 or rpn >= 120:
        return "high_priority_mitigation"
    if rpn >= 60:
        return "planned_mitigation"
    return "monitor_and_verify"


def analyze_fault_propagation(
    blueprint: SystemBlueprint,
    *,
    additional_faults: Sequence[FaultMode] = (),
) -> FaultPropagationReport:
    blueprint.validate()
    component_map = blueprint.component_map()
    adjacency: dict[str, set[str]] = {component_id: set() for component_id in component_map}
    incoming: dict[str, int] = {component_id: 0 for component_id in component_map}
    for connection in blueprint.connections:
        adjacency[connection.source_component].add(connection.target_component)
        incoming[connection.target_component] += 1
    faults = tuple(blueprint.fault_modes) + tuple(additional_faults)
    if not faults:
        raise ValueError("fault propagation requires at least one fault mode")
    seen_ids: set[str] = set()
    records: list[FaultPropagationRecord] = []
    for fault in faults:
        fault.validate()
        if fault.fault_id in seen_ids:
            raise ValueError("duplicate fault_id in propagation input")
        seen_ids.add(fault.fault_id)
        if fault.component_id not in component_map:
            raise ValueError("fault references an unknown component")
        queue: list[tuple[str, int]] = [(fault.component_id, 0)]
        visited: dict[str, int] = {}
        while queue:
            component_id, depth = queue.pop(0)
            if component_id in visited and visited[component_id] <= depth:
                continue
            visited[component_id] = depth
            for target in sorted(adjacency[component_id]):
                queue.append((target, depth + 1))
        affected = tuple(sorted(visited, key=lambda item: (visited[item], item)))
        affected_domains = tuple(
            sorted({domain for component_id in affected for domain in component_map[component_id].domains})
        )
        critical = tuple(
            item for item in affected if component_map[item].criticality >= 4
        )
        source = component_map[fault.component_id]
        single_point = source.criticality >= 4 and incoming[fault.component_id] <= 1
        records.append(
            FaultPropagationRecord(
                fault=fault,
                affected_components=affected,
                affected_domains=affected_domains,
                propagation_depth=max(visited.values()),
                critical_components_reached=critical,
                single_point_risk=single_point,
                mitigation_priority=_mitigation_priority(fault, len(critical), single_point),
            )
        )
    highest_rpn = max(item.fault.risk_priority_number for item in records)
    single_points = sum(item.single_point_risk for item in records)
    critical_paths = sum(bool(item.critical_components_reached) for item in records)
    normalized_risk = sum(min(item.fault.risk_priority_number / 1000.0, 1.0) for item in records) / len(records)
    spread_penalty = sum(
        len(item.affected_components) / len(component_map) for item in records
    ) / len(records)
    single_penalty = single_points / len(records)
    resilience = max(0.0, min(1.0, 1.0 - 0.45 * normalized_risk - 0.35 * spread_penalty - 0.20 * single_penalty))
    payload = {
        "system_id": blueprint.system_id,
        "records": [item.to_dict() for item in records],
        "heuristic_resilience_score": resilience,
    }
    return FaultPropagationReport(
        system_id=blueprint.system_id,
        records=tuple(records),
        highest_rpn=highest_rpn,
        single_point_risk_count=single_points,
        critical_path_count=critical_paths,
        heuristic_resilience_score=resilience,
        evidence_hash=_stable_hash(payload),
    )
