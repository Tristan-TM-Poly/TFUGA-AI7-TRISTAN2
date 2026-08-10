from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MaterialOffer:
    actor: str
    material: str
    quantity_kg: float
    purity: float
    unit_price: float
    distance_km: float = 0.0

    def __post_init__(self) -> None:
        if self.quantity_kg <= 0:
            raise ValueError("offer quantity must be positive")
        if not 0 <= self.purity <= 1:
            raise ValueError("purity must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class MaterialNeed:
    actor: str
    material: str
    quantity_kg: float
    min_purity: float
    max_unit_price: float

    def __post_init__(self) -> None:
        if self.quantity_kg <= 0:
            raise ValueError("need quantity must be positive")
        if not 0 <= self.min_purity <= 1:
            raise ValueError("min_purity must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class SymbiosisMatch:
    seller: str
    buyer: str
    material: str
    quantity_kg: float
    effective_unit_cost: float


def match_material_flows(offers: tuple[MaterialOffer, ...], needs: tuple[MaterialNeed, ...], *, transport_cost_per_kg_km: float = 0.0) -> tuple[SymbiosisMatch, ...]:
    """Greedy transparent matcher for compatible secondary-material flows."""
    if transport_cost_per_kg_km < 0:
        raise ValueError("transport cost must be non-negative")
    remaining_offer = {i: offer.quantity_kg for i, offer in enumerate(offers)}
    remaining_need = {i: need.quantity_kg for i, need in enumerate(needs)}
    candidates: list[tuple[float, int, int]] = []
    for oi, offer in enumerate(offers):
        for ni, need in enumerate(needs):
            if offer.actor == need.actor or offer.material != need.material:
                continue
            if offer.purity < need.min_purity:
                continue
            effective = offer.unit_price + transport_cost_per_kg_km * offer.distance_km
            if effective <= need.max_unit_price:
                candidates.append((effective, oi, ni))
    candidates.sort(key=lambda item: (item[0], offers[item[1]].actor, needs[item[2]].actor))
    matches: list[SymbiosisMatch] = []
    for effective, oi, ni in candidates:
        quantity = min(remaining_offer[oi], remaining_need[ni])
        if quantity <= 0:
            continue
        offer = offers[oi]
        need = needs[ni]
        matches.append(SymbiosisMatch(seller=offer.actor, buyer=need.actor, material=offer.material, quantity_kg=quantity, effective_unit_cost=effective))
        remaining_offer[oi] -= quantity
        remaining_need[ni] -= quantity
    return tuple(matches)
