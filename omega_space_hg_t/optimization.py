"""Adaptive, resumable design-space exploration for Ω-SPACE-HG-T∞.

The address space has no artificial permanent maximum. Each execution remains
bounded by an explicit count, budget and the host's physical resources.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable

from .mission import simulate_mission
from .models import MissionConfig


@dataclass(frozen=True)
class DesignAddress:
    logical_index: int
    panel_scale: float
    battery_scale: float
    radiator_scale: float
    payload_duty_cycle: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DesignEvaluation:
    address: DesignAddress
    wet_mass_proxy_kg: float
    minimum_battery_fraction: float
    maximum_temperature_k: float
    maximum_stored_data_fraction: float
    energy_drift_fraction: float
    safe: bool
    violations: tuple[str, ...]
    objective_vector: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["address"] = self.address.to_dict()
        payload["violations"] = list(self.violations)
        payload["objective_vector"] = list(self.objective_vector)
        return payload


def radical_inverse(index: int, base: int) -> float:
    if index < 0:
        raise ValueError("index cannot be negative")
    if base < 2:
        raise ValueError("base must be at least two")
    value = 0.0
    factor = 1.0 / base
    current = index + 1
    while current:
        current, digit = divmod(current, base)
        value += digit * factor
        factor /= base
    return value


class UnboundedDesignFrontier:
    """Map every non-negative integer to one deterministic architecture."""

    permanent_total_cap = None

    def decode(self, logical_index: int) -> DesignAddress:
        if logical_index < 0:
            raise ValueError("logical_index cannot be negative")
        panel = 0.55 + 1.90 * radical_inverse(logical_index, 2)
        battery = 0.55 + 1.90 * radical_inverse(logical_index, 3)
        radiator = 0.55 + 1.90 * radical_inverse(logical_index, 5)
        duty = 0.08 + 0.72 * radical_inverse(logical_index, 7)
        return DesignAddress(logical_index, panel, battery, radiator, duty)

    def plan(self, start_offset: int, count: int) -> dict[str, Any]:
        if start_offset < 0 or count < 0:
            raise ValueError("start_offset and count must be non-negative")
        addresses = [self.decode(start_offset + index).to_dict() for index in range(count)]
        return {
            "frontier": "unbounded-low-discrepancy-v1",
            "start_offset": start_offset,
            "count": count,
            "next_offset": start_offset + count,
            "permanent_total_cap": self.permanent_total_cap,
            "addresses": addresses,
            "claim_boundary": "addressable designs are not executed or qualified spacecraft",
        }


def apply_design(config: MissionConfig, address: DesignAddress) -> MissionConfig:
    spacecraft = replace(
        config.spacecraft,
        panel_area_m2=config.spacecraft.panel_area_m2 * address.panel_scale,
        battery_capacity_wh=config.spacecraft.battery_capacity_wh * address.battery_scale,
        radiator_area_m2=config.spacecraft.radiator_area_m2 * address.radiator_scale,
    )
    return replace(config, spacecraft=spacecraft, payload_duty_cycle=address.payload_duty_cycle)


def evaluate_design(config: MissionConfig, address: DesignAddress) -> DesignEvaluation:
    candidate = apply_design(config, address)
    result = simulate_mission(candidate)
    # Transparent early-design mass proxy; it is not a detailed mass model.
    mass_proxy = (
        candidate.spacecraft.wet_mass_kg
        + 2.6 * candidate.spacecraft.panel_area_m2
        + 0.015 * candidate.spacecraft.battery_capacity_wh
        + 1.8 * candidate.spacecraft.radiator_area_m2
    )
    metrics = result.metrics
    unsafe_penalty = 1.0 if metrics.safe else 10.0 + len(metrics.violations)
    objective = (
        mass_proxy,
        unsafe_penalty,
        1.0 - metrics.minimum_battery_fraction,
        metrics.maximum_stored_data_fraction,
        max(0.0, metrics.maximum_temperature_k - 300.0),
    )
    return DesignEvaluation(
        address=address,
        wet_mass_proxy_kg=mass_proxy,
        minimum_battery_fraction=metrics.minimum_battery_fraction,
        maximum_temperature_k=metrics.maximum_temperature_k,
        maximum_stored_data_fraction=metrics.maximum_stored_data_fraction,
        energy_drift_fraction=metrics.energy_drift_fraction,
        safe=metrics.safe,
        violations=metrics.violations,
        objective_vector=objective,
    )


def dominates(left: DesignEvaluation, right: DesignEvaluation) -> bool:
    pairs = tuple(zip(left.objective_vector, right.objective_vector))
    return all(a <= b for a, b in pairs) and any(a < b for a, b in pairs)


def pareto_front(evaluations: Iterable[DesignEvaluation]) -> tuple[DesignEvaluation, ...]:
    values = tuple(evaluations)
    front = [candidate for candidate in values if not any(dominates(other, candidate) for other in values if other is not candidate)]
    return tuple(sorted(front, key=lambda item: item.objective_vector))


def optimize_designs(config: MissionConfig, start_offset: int = 0, count: int = 32) -> dict[str, Any]:
    frontier = UnboundedDesignFrontier()
    addresses = [frontier.decode(start_offset + index) for index in range(count)]
    evaluations = tuple(evaluate_design(config, address) for address in addresses)
    front = pareto_front(evaluations)
    return {
        "frontier": {
            "type": "unbounded-low-discrepancy-v1",
            "start_offset": start_offset,
            "evaluated_count": count,
            "next_offset": start_offset + count,
            "permanent_total_cap": None,
        },
        "pareto_count": len(front),
        "pareto_front": [item.to_dict() for item in front],
        "evaluations": [item.to_dict() for item in evaluations],
        "flight_qualified_claimed": False,
        "scientific_validation_claimed": False,
    }
