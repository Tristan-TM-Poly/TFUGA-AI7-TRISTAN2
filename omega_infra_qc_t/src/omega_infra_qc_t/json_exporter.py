"""Deterministic JSON export for InfrastructureGraph Quebec."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from .evidence import EvidenceGraph
from .infra_graph import InfraGraph
from .maintenance import MaintenanceSignal
from .oak_security_gate import SecurityGateResult
from .resilience import ResilienceScenario
from .risk_tensor import InfraRiskTensor
from .source_registry import SourceRegistry


@dataclass(frozen=True)
class InfraExportBundle:
    graph: InfraGraph
    sources: SourceRegistry
    evidence: EvidenceGraph
    risks: List[InfraRiskTensor] = field(default_factory=list)
    maintenance: List[MaintenanceSignal] = field(default_factory=list)
    scenarios: List[ResilienceScenario] = field(default_factory=list)
    security_gate: SecurityGateResult | None = None
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, public_safe: bool = True) -> Dict[str, Any]:
        return {
            "schema": "omega_infra_qc_t.export_bundle.v0",
            "generated_at": self.generated_at,
            "public_safe": public_safe,
            "graph": self.graph.export_json_dict(public_safe=public_safe),
            "sources": self.sources.to_dict(),
            "evidence": self.evidence.to_dict(),
            "risks": [risk.to_dict() for risk in self.risks],
            "maintenance": [signal.to_dict() for signal in self.maintenance],
            "scenarios": [scenario.to_dict(public_safe=public_safe) for scenario in self.scenarios],
            "security_gate": self.security_gate.to_dict() if self.security_gate else None,
            "metadata": dict(self.metadata),
            "oak_note": "Export bundle is review support, not final authority.",
        }


class JsonExporter:
    """Canonical JSON serialization utilities."""

    @staticmethod
    def canonical_json(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def export_bundle(self, bundle: InfraExportBundle, *, public_safe: bool = True) -> str:
        return self.canonical_json(bundle.to_dict(public_safe=public_safe))
