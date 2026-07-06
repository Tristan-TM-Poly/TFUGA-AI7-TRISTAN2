"""Deterministic JSON exporter for TristanGovGraph Quebec."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .evidence import EvidenceGraph
from .gov_graph import GovGraph
from .m_minus import MMinusRegister
from .product_factory import ProductFactory
from .risk import RiskRegister
from .service_model import ServiceCatalog
from .source_registry import SourceRegistry


@dataclass(frozen=True)
class ExportBundle:
    """A deterministic export bundle for OAK review."""

    name: str
    graph: Optional[GovGraph] = None
    sources: Optional[SourceRegistry] = None
    evidence: Optional[EvidenceGraph] = None
    risks: Optional[RiskRegister] = None
    services: Optional[ServiceCatalog] = None
    products: Optional[ProductFactory] = None
    m_minus: Optional[MMinusRegister] = None
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.export_bundle.v0",
            "name": self.name,
            "generated_at": self.generated_at,
            "metadata": dict(self.metadata),
            "graph": self.graph.export_json_dict() if self.graph else None,
            "sources": self.sources.to_dict() if self.sources else None,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "risks": self.risks.to_dict() if self.risks else None,
            "services": self.services.to_dict() if self.services else None,
            "products": self.products.to_dict() if self.products else None,
            "m_minus": self.m_minus.to_dict() if self.m_minus else None,
            "oak_note": "Export bundle is for review, reproducibility and traceability.",
        }


class JsonExporter:
    """Render deterministic JSON text for OAK artifacts."""

    def canonical_json(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def export_bundle(self, bundle: ExportBundle) -> str:
        return self.canonical_json(bundle.to_dict())
