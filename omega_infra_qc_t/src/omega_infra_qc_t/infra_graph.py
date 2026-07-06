"""Infrastructure graph model for Quebec infrastructure MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from .asset_model import AssetNode

DependencyKind = Literal[
    "depends_on",
    "feeds",
    "connects_to",
    "backs_up",
    "serves",
    "shares_operator",
    "shares_region",
    "other",
]


@dataclass(frozen=True)
class DependencyEdge:
    """A non-sensitive dependency relation between assets."""

    source_asset_id: str
    target_asset_id: str
    kind: DependencyKind = "depends_on"
    confidence: float = 0.5
    visibility: str = "public"
    evidence_ids: List[str] = field(default_factory=list)
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.source_asset_id.strip():
            errors.append("source_asset_id is required")
        if not self.target_asset_id.strip():
            errors.append("target_asset_id is required")
        if self.kind not in DependencyKind.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid dependency kind: {self.kind}")
        if not 0 <= self.confidence <= 1:
            errors.append("confidence must be between 0 and 1")
        return errors

    @property
    def is_sensitive(self) -> bool:
        return self.visibility in {"restricted", "critical"}

    def to_dict(self, *, public_safe: bool = False) -> Dict[str, Any]:
        notes = "redacted" if public_safe and self.is_sensitive else self.notes
        return {
            "source_asset_id": self.source_asset_id,
            "target_asset_id": self.target_asset_id,
            "kind": self.kind,
            "confidence": self.confidence,
            "visibility": self.visibility,
            "evidence_ids": list(self.evidence_ids),
            "notes": notes,
            "metadata": {} if public_safe and self.is_sensitive else dict(self.metadata),
        }


class InfraGraph:
    """OAK-safe graph of infrastructure assets and dependencies."""

    def __init__(self) -> None:
        self.assets: Dict[str, AssetNode] = {}
        self.dependencies: List[DependencyEdge] = []
        self.m_minus: List[Dict[str, Any]] = []

    def add_asset(self, asset: AssetNode) -> None:
        errors = asset.validate()
        if errors:
            raise ValueError("Invalid AssetNode: " + "; ".join(errors))
        if asset.asset_id in self.assets:
            self.m_minus.append({"type": "duplicate_asset", "asset_id": asset.asset_id})
            raise ValueError(f"duplicate asset_id: {asset.asset_id}")
        self.assets[asset.asset_id] = asset

    def add_dependency(self, edge: DependencyEdge) -> None:
        errors = edge.validate()
        if errors:
            raise ValueError("Invalid DependencyEdge: " + "; ".join(errors))
        if edge.source_asset_id not in self.assets:
            raise ValueError(f"unknown source asset: {edge.source_asset_id}")
        if edge.target_asset_id not in self.assets:
            raise ValueError(f"unknown target asset: {edge.target_asset_id}")
        self.dependencies.append(edge)

    def assets_by_sector(self, sector: str) -> List[AssetNode]:
        return [asset for asset in self.assets.values() if asset.sector == sector]

    def sensitive_assets(self) -> List[AssetNode]:
        return [asset for asset in self.assets.values() if asset.is_sensitive]

    def sensitive_dependencies(self) -> List[DependencyEdge]:
        return [edge for edge in self.dependencies if edge.is_sensitive]

    def quality_report(self) -> Dict[str, Any]:
        sectors: Dict[str, int] = {}
        for asset in self.assets.values():
            sectors[asset.sector] = sectors.get(asset.sector, 0) + 1
        return {
            "asset_count": len(self.assets),
            "dependency_count": len(self.dependencies),
            "sectors": sectors,
            "sensitive_asset_count": len(self.sensitive_assets()),
            "sensitive_dependency_count": len(self.sensitive_dependencies()),
            "m_minus_count": len(self.m_minus),
        }

    def export_json_dict(self, *, public_safe: bool = True) -> Dict[str, Any]:
        return {
            "schema": "omega_infra_qc_t.infra_graph.v0",
            "assets": [asset.to_dict(public_safe=public_safe) for asset in self.assets.values()],
            "dependencies": [edge.to_dict(public_safe=public_safe) for edge in self.dependencies],
            "quality": self.quality_report(),
            "oak_note": "InfrastructureGraph output is review support, not final authority.",
        }
