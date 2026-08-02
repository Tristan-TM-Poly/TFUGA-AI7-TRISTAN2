from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class IsotropicElasticity:
    young_pa: float
    poisson: float

    def __post_init__(self) -> None:
        if self.young_pa <= 0:
            raise ValueError("Young's modulus must be positive")
        if not -1 < self.poisson < 0.5:
            raise ValueError("Poisson ratio must be within (-1, 0.5)")

    @property
    def shear_pa(self) -> float:
        return self.young_pa / (2 * (1 + self.poisson))

    @property
    def bulk_pa(self) -> float:
        return self.young_pa / (3 * (1 - 2 * self.poisson))

    @property
    def lame_lambda_pa(self) -> float:
        return self.young_pa * self.poisson / (
            (1 + self.poisson) * (1 - 2 * self.poisson)
        )

    def stiffness_voigt(self) -> tuple[tuple[float, ...], ...]:
        lam = self.lame_lambda_pa
        mu = self.shear_pa
        return (
            (lam + 2 * mu, lam, lam, 0.0, 0.0, 0.0),
            (lam, lam + 2 * mu, lam, 0.0, 0.0, 0.0),
            (lam, lam, lam + 2 * mu, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, mu, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0, mu, 0.0),
            (0.0, 0.0, 0.0, 0.0, 0.0, mu),
        )

    def stress(self, strain_voigt: Sequence[float]) -> tuple[float, ...]:
        if len(strain_voigt) != 6:
            raise ValueError("Voigt strain requires six components")
        stiffness = self.stiffness_voigt()
        return tuple(
            sum(stiffness[row][column] * float(strain_voigt[column]) for column in range(6))
            for row in range(6)
        )


def rule_of_mixtures(
    values: Iterable[float], fractions: Iterable[float], *, mode: str = "voigt"
) -> float:
    property_values = tuple(float(value) for value in values)
    weights = tuple(float(value) for value in fractions)
    if len(property_values) != len(weights) or not property_values:
        raise ValueError("Values and fractions must be non-empty and have equal length")
    if any(value <= 0 for value in property_values):
        raise ValueError("Property values must be positive")
    if any(weight < 0 for weight in weights):
        raise ValueError("Fractions cannot be negative")
    total = sum(weights)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError("Fractions must sum to one")
    normalized_mode = mode.lower()
    if normalized_mode == "voigt":
        return sum(value * weight for value, weight in zip(property_values, weights))
    if normalized_mode == "reuss":
        return 1.0 / sum(weight / value for value, weight in zip(property_values, weights))
    if normalized_mode in {"hill", "voigt-reuss-hill"}:
        voigt = rule_of_mixtures(property_values, weights, mode="voigt")
        reuss = rule_of_mixtures(property_values, weights, mode="reuss")
        return 0.5 * (voigt + reuss)
    raise ValueError(f"Unsupported mixture mode: {mode}")


def hall_petch_strength(
    sigma_0_pa: float,
    coefficient_pa_sqrt_m: float,
    grain_size_m: float,
) -> float:
    if sigma_0_pa < 0 or coefficient_pa_sqrt_m < 0 or grain_size_m <= 0:
        raise ValueError("Hall-Petch inputs must be nonnegative and grain size positive")
    return sigma_0_pa + coefficient_pa_sqrt_m / math.sqrt(grain_size_m)


def gibson_ashby_modulus(
    solid_modulus_pa: float,
    relative_density: float,
    *,
    coefficient: float = 1.0,
    exponent: float = 2.0,
) -> float:
    if solid_modulus_pa <= 0:
        raise ValueError("Solid modulus must be positive")
    if not 0 <= relative_density <= 1:
        raise ValueError("Relative density must be within [0, 1]")
    if coefficient < 0 or exponent <= 0:
        raise ValueError("Coefficient must be nonnegative and exponent positive")
    return coefficient * solid_modulus_pa * relative_density**exponent


def thermal_strain(
    expansion_per_k: float | Sequence[Sequence[float]],
    delta_temperature_k: float,
) -> tuple[tuple[float, ...], ...]:
    if isinstance(expansion_per_k, (int, float)):
        alpha = float(expansion_per_k)
        return (
            (alpha * delta_temperature_k, 0.0, 0.0),
            (0.0, alpha * delta_temperature_k, 0.0),
            (0.0, 0.0, alpha * delta_temperature_k),
        )
    rows = [tuple(float(value) for value in row) for row in expansion_per_k]
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("Thermal expansion tensor must be 3x3")
    return tuple(
        tuple(value * delta_temperature_k for value in row) for row in rows
    )


def von_mises_stress(stress_voigt: Sequence[float]) -> float:
    if len(stress_voigt) != 6:
        raise ValueError("Voigt stress requires six components")
    sx, sy, sz, txy, tyz, txz = map(float, stress_voigt)
    return math.sqrt(
        0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2)
        + 3.0 * (txy**2 + tyz**2 + txz**2)
    )


def fracture_safety_factor(
    fracture_toughness_pa_sqrt_m: float,
    applied_stress_pa: float,
    crack_half_length_m: float,
    *,
    geometry_factor: float = 1.0,
) -> float:
    if fracture_toughness_pa_sqrt_m <= 0:
        raise ValueError("Fracture toughness must be positive")
    if applied_stress_pa < 0 or crack_half_length_m <= 0 or geometry_factor <= 0:
        raise ValueError("Stress must be nonnegative; crack length and geometry factor positive")
    intensity = geometry_factor * applied_stress_pa * math.sqrt(
        math.pi * crack_half_length_m
    )
    if intensity == 0:
        return float("inf")
    return fracture_toughness_pa_sqrt_m / intensity
