from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import Component, RecoveryRoute


@dataclass(frozen=True, slots=True)
class InventoryFlow:
    name: str
    amount: float
    unit: str
    direction: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("inventory amount must be non-negative")
        if self.direction not in {"input", "output", "waste"}:
            raise ValueError("direction must be input, output or waste")


@dataclass(frozen=True, slots=True)
class LCAInventory:
    component_id: str
    route_mode: str
    flows: tuple[InventoryFlow, ...]
    claim_boundary: str = "inventory_only_no_lifecycle_impact_claim"

    def to_dict(self) -> dict:
        return asdict(self)


def inventory_for_route(component: Component, route: RecoveryRoute) -> LCAInventory:
    """Create an LCI-shaped inventory without performing impact assessment."""
    retained = component.mass_kg * route.retained_mass_fraction
    residual = max(0.0, component.mass_kg - retained)
    energy = component.disassembly_energy_kwh + route.energy_kwh
    flows = (
        InventoryFlow("component_mass", component.mass_kg, "kg", "input"),
        InventoryFlow("electricity", energy, "kWh", "input"),
        InventoryFlow("retained_product_mass", retained, "kg", "output"),
        InventoryFlow("residual_mass", residual, "kg", "waste"),
    )
    return LCAInventory(component_id=component.component_id, route_mode=route.mode.value, flows=flows)
