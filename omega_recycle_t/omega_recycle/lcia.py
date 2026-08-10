from __future__ import annotations

from dataclasses import dataclass

from .lca import LCAInventory
from .provenance import ProvenanceRecord


@dataclass(frozen=True, slots=True)
class CharacterizationFactor:
    flow_name: str
    flow_unit: str
    category: str
    factor: float
    result_unit: str
    direction: str | None = None

    def __post_init__(self) -> None:
        if not self.flow_name or not self.flow_unit or not self.category or not self.result_unit:
            raise ValueError("characterization factor metadata is required")
        if self.direction is not None and self.direction not in {"input", "output", "waste"}:
            raise ValueError("direction must be input, output, waste or None")


@dataclass(frozen=True, slots=True)
class CharacterizationSet:
    name: str
    version: str
    methodology: str
    provenance: ProvenanceRecord
    factors: tuple[CharacterizationFactor, ...]
    externally_supplied: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.methodology:
            raise ValueError("characterization set metadata is required")


@dataclass(frozen=True, slots=True)
class ImpactScore:
    category: str
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class CharacterizationResult:
    inventory_component_id: str
    inventory_route_mode: str
    factor_set_name: str
    factor_set_version: str
    impacts: tuple[ImpactScore, ...]
    matched_flows: int
    unmatched_flows: tuple[str, ...]
    claim_boundary: str = "screening_characterization_only_not_certified_lca_or_environmental_superiority"


def characterize_inventory(inventory: LCAInventory, factor_set: CharacterizationSet) -> CharacterizationResult:
    """Apply an externally supplied, provenance-bound characterization set.

    R0.4 provides an adapter/accounting court only. No built-in factor set is
    endorsed and this function does not certify lifecycle conclusions.
    """
    totals: dict[tuple[str, str], float] = {}
    matched_flow_indices: set[int] = set()
    for index, flow in enumerate(inventory.flows):
        for factor in factor_set.factors:
            if factor.flow_name != flow.name or factor.flow_unit != flow.unit:
                continue
            if factor.direction is not None and factor.direction != flow.direction:
                continue
            key = (factor.category, factor.result_unit)
            totals[key] = totals.get(key, 0.0) + flow.amount * factor.factor
            matched_flow_indices.add(index)

    impacts = tuple(
        ImpactScore(category=category, value=value, unit=unit)
        for (category, unit), value in sorted(totals.items())
    )
    unmatched = tuple(
        f"{flow.direction}:{flow.name}[{flow.unit}]"
        for index, flow in enumerate(inventory.flows)
        if index not in matched_flow_indices
    )
    return CharacterizationResult(
        inventory_component_id=inventory.component_id,
        inventory_route_mode=inventory.route_mode,
        factor_set_name=factor_set.name,
        factor_set_version=factor_set.version,
        impacts=impacts,
        matched_flows=len(matched_flow_indices),
        unmatched_flows=unmatched,
    )
