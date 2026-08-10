from __future__ import annotations

import math
from dataclasses import dataclass

from .models import Component, Material, PRESERVATION_RANK, RecoveryMode, RecoveryRoute, RouteEvaluation


@dataclass(frozen=True, slots=True)
class ScoringPolicy:
    energy_shadow_price_per_kwh: float = 0.15
    risk_penalty: float = 20.0
    preservation_bonus: float = 0.8
    future_cycle_weight: float = 0.5

    def __post_init__(self) -> None:
        if min(self.energy_shadow_price_per_kwh, self.risk_penalty, self.preservation_bonus, self.future_cycle_weight) < 0:
            raise ValueError("scoring weights must be non-negative")


def material_entropy(component: Component) -> float:
    """Normalized Shannon entropy of the component material mixture."""
    fractions = [p for p in component.material_fractions.values() if p > 0]
    if len(fractions) <= 1:
        return 0.0
    raw = -sum(p * math.log(p) for p in fractions)
    return raw / math.log(len(fractions))


def _material_recovery_value(component: Component, materials: dict[str, Material], route: RecoveryRoute) -> float:
    value = 0.0
    for name, fraction in component.material_fractions.items():
        material = materials[name]
        clean_fraction = fraction * (1.0 - component.contamination)
        value += component.mass_kg * clean_fraction * material.unit_value_per_kg * material.purity * route.retained_mass_fraction * route.output_quality
    return value


def recovered_value(component: Component, materials: dict[str, Material], route: RecoveryRoute) -> float:
    q = route.output_quality
    fp = component.functional_probability
    if route.mode is RecoveryMode.REUSE:
        return component.reuse_value * fp * q
    if route.mode is RecoveryMode.REPAIR:
        return component.reuse_value * min(1.0, fp + 0.25) * q
    if route.mode is RecoveryMode.REMANUFACTURE:
        return component.reuse_value * min(1.0, fp + 0.40) * 0.9 * q
    if route.mode is RecoveryMode.COMPONENT_HARVEST:
        return component.reuse_value * fp * 0.72 * q
    if route.mode is RecoveryMode.MATERIAL_RECYCLE:
        return _material_recovery_value(component, materials, route)
    if route.mode is RecoveryMode.ENERGY_RECOVERY:
        return 0.05 * component.mass_kg * route.retained_mass_fraction
    return 0.0


def evaluate_route(component: Component, materials: dict[str, Material], route: RecoveryRoute, policy: ScoringPolicy | None = None) -> RouteEvaluation:
    policy = policy or ScoringPolicy()
    value = recovered_value(component, materials, route)
    total_cost = component.disassembly_cost + route.process_cost + policy.energy_shadow_price_per_kwh * (component.disassembly_energy_kwh + route.energy_kwh) + route.externality_penalty + policy.risk_penalty * route.risk
    preservation = policy.preservation_bonus * PRESERVATION_RANK[route.mode] * route.output_quality
    future = policy.future_cycle_weight * component.expected_future_cycles * route.output_quality
    score = value - total_cost + preservation + future
    warnings: list[str] = []
    dry_run_only = False
    if component.hazardous or route.requires_certified_process:
        dry_run_only = True
        warnings.append("certified_process_or_professional_handling_required")
    if route.mode is RecoveryMode.DISPOSAL:
        warnings.append("lowest_structure_preservation_route")
    return RouteEvaluation(component_id=component.component_id, mode=route.mode, recovered_value=value, total_cost=total_cost, retained_mass_kg=component.mass_kg * route.retained_mass_fraction, score=score, dry_run_only=dry_run_only, warnings=tuple(warnings))


def circularity_score(*, recovered_value_value: float, input_value: float, retained_mass_kg: float, input_mass_kg: float, output_quality: float, expected_future_cycles: float) -> float:
    if input_value < 0 or input_mass_kg <= 0:
        raise ValueError("input_value must be non-negative and input_mass_kg positive")
    value_ratio = 1.0 if input_value == 0 and recovered_value_value > 0 else (recovered_value_value / input_value if input_value else 0.0)
    mass_ratio = retained_mass_kg / input_mass_kg
    cycle_term = expected_future_cycles / (1.0 + expected_future_cycles)
    raw = 0.35 * value_ratio + 0.30 * mass_ratio + 0.20 * output_quality + 0.15 * cycle_term
    return max(0.0, min(1.0, raw))
