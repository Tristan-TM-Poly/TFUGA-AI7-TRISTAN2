"""Infrastructure asset primitives for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

OwnerType = Literal["public", "private", "municipal", "mixed", "community", "unknown"]
VisibilityTier = Literal["public", "review", "restricted", "critical"]
AssetSector = Literal[
    "water",
    "transport",
    "energy",
    "telecom",
    "health",
    "education",
    "government",
    "food",
    "housing",
    "data",
    "industrial",
    "community",
    "other",
]


@dataclass(frozen=True)
class AssetNode:
    """A safe, review-first infrastructure asset node."""

    asset_id: str
    name: str
    sector: AssetSector = "other"
    owner_type: OwnerType = "unknown"
    operator: str = "unknown"
    region: str = "unknown"
    municipality: str = "unknown"
    location_level: str = "generalized"
    visibility: VisibilityTier = "public"
    criticality: int = 0
    public_dependency: int = 0
    condition_status: str = "unknown"
    source_ids: List[str] = field(default_factory=list)
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.asset_id.strip():
            errors.append("asset_id is required")
        if not self.name.strip():
            errors.append("name is required")
        if self.sector not in AssetSector.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid sector: {self.sector}")
        if self.owner_type not in OwnerType.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid owner_type: {self.owner_type}")
        if self.visibility not in VisibilityTier.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid visibility: {self.visibility}")
        if not 0 <= self.criticality <= 5:
            errors.append("criticality must be between 0 and 5")
        if not 0 <= self.public_dependency <= 5:
            errors.append("public_dependency must be between 0 and 5")
        return errors

    @property
    def is_sensitive(self) -> bool:
        return self.visibility in {"restricted", "critical"} or self.criticality >= 4

    @property
    def public_safe_summary(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name if self.visibility == "public" else "redacted_asset",
            "sector": self.sector,
            "owner_type": self.owner_type,
            "region": self.region,
            "municipality": self.municipality if self.visibility == "public" else "redacted",
            "location_level": self.location_level,
            "visibility": self.visibility,
            "criticality": self.criticality,
            "public_dependency": self.public_dependency,
            "condition_status": self.condition_status,
            "notes": self.notes if self.visibility == "public" else "redacted",
        }

    def to_dict(self, *, public_safe: bool = False) -> Dict[str, Any]:
        if public_safe:
            return dict(self.public_safe_summary)
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "sector": self.sector,
            "owner_type": self.owner_type,
            "operator": self.operator,
            "region": self.region,
            "municipality": self.municipality,
            "location_level": self.location_level,
            "visibility": self.visibility,
            "criticality": self.criticality,
            "public_dependency": self.public_dependency,
            "condition_status": self.condition_status,
            "source_ids": list(self.source_ids),
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }
