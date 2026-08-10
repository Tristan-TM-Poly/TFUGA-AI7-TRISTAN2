from __future__ import annotations

from dataclasses import dataclass

from .network import DemandNode, SupplyNode, TransferArc, min_cost_transport
from .symbiosis import MaterialNeed, MaterialOffer, SymbiosisMatch, match_material_flows


@dataclass(frozen=True, slots=True)
class SymbiosisOptimizationResult:
    matches: tuple[SymbiosisMatch, ...]
    total_quantity_kg: float
    total_cost: float
    unmet_demand_kg: float
    unused_supply_kg: float
    optimality_certified: bool = True


@dataclass(frozen=True, slots=True)
class SymbiosisRegretReport:
    greedy_quantity_kg: float
    exact_quantity_kg: float
    greedy_cost: float
    exact_cost: float
    quantity_regret_kg: float
    comparable_cost_regret: float | None
    greedy_is_flow_optimal: bool
    greedy_is_cost_optimal_given_equal_flow: bool | None


def exact_match_material_flows(
    offers: tuple[MaterialOffer, ...],
    needs: tuple[MaterialNeed, ...],
    *,
    transport_cost_per_kg_km: float = 0.0,
) -> SymbiosisOptimizationResult:
    """Exact max-quantity/min-cost matcher using the R0.2 compatibility rules."""
    if transport_cost_per_kg_km < 0:
        raise ValueError("transport cost must be non-negative")

    supplies = tuple(SupplyNode(f"offer:{i}", offer.quantity_kg) for i, offer in enumerate(offers))
    demands = tuple(DemandNode(f"need:{i}", need.quantity_kg) for i, need in enumerate(needs))
    arcs: list[TransferArc] = []
    for oi, offer in enumerate(offers):
        for ni, need in enumerate(needs):
            if offer.actor == need.actor or offer.material != need.material:
                continue
            if offer.purity < need.min_purity:
                continue
            effective = offer.unit_price + transport_cost_per_kg_km * offer.distance_km
            if effective <= need.max_unit_price:
                arcs.append(
                    TransferArc(
                        source_id=f"offer:{oi}",
                        target_id=f"need:{ni}",
                        capacity=min(offer.quantity_kg, need.quantity_kg),
                        unit_cost=effective,
                        label=f"{offer.material}:{oi}:{ni}",
                    )
                )

    result = min_cost_transport(supplies, demands, tuple(arcs))
    matches = []
    for allocation in result.allocations:
        oi = int(allocation.source_id.split(":", 1)[1])
        ni = int(allocation.target_id.split(":", 1)[1])
        offer = offers[oi]
        need = needs[ni]
        matches.append(
            SymbiosisMatch(
                seller=offer.actor,
                buyer=need.actor,
                material=offer.material,
                quantity_kg=allocation.quantity,
                effective_unit_cost=allocation.unit_cost,
            )
        )
    matches.sort(key=lambda item: (item.seller, item.buyer, item.material, item.effective_unit_cost))
    return SymbiosisOptimizationResult(
        matches=tuple(matches),
        total_quantity_kg=result.total_flow,
        total_cost=result.total_cost,
        unmet_demand_kg=result.unmet_demand,
        unused_supply_kg=result.unused_supply,
        optimality_certified=result.optimality_certified,
    )


def symbiosis_regret(
    offers: tuple[MaterialOffer, ...],
    needs: tuple[MaterialNeed, ...],
    *,
    transport_cost_per_kg_km: float = 0.0,
) -> SymbiosisRegretReport:
    greedy = match_material_flows(offers, needs, transport_cost_per_kg_km=transport_cost_per_kg_km)
    exact = exact_match_material_flows(offers, needs, transport_cost_per_kg_km=transport_cost_per_kg_km)
    greedy_quantity = sum(match.quantity_kg for match in greedy)
    greedy_cost = sum(match.quantity_kg * match.effective_unit_cost for match in greedy)
    eps = 1e-9
    equal_flow = abs(greedy_quantity - exact.total_quantity_kg) <= eps
    cost_regret = greedy_cost - exact.total_cost if equal_flow else None
    return SymbiosisRegretReport(
        greedy_quantity_kg=greedy_quantity,
        exact_quantity_kg=exact.total_quantity_kg,
        greedy_cost=greedy_cost,
        exact_cost=exact.total_cost,
        quantity_regret_kg=max(0.0, exact.total_quantity_kg - greedy_quantity),
        comparable_cost_regret=cost_regret,
        greedy_is_flow_optimal=equal_flow,
        greedy_is_cost_optimal_given_equal_flow=(cost_regret is not None and cost_regret <= eps) if equal_flow else None,
    )
