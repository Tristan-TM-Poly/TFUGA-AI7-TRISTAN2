from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class EnergyTerm:
    name: str
    evaluator: Callable[[Mapping[str, float]], float]
    unit: str = "J"
    established: bool = False
    assumptions: tuple[str, ...] = ()
    domain: Mapping[str, tuple[float | None, float | None]] = field(default_factory=dict)

    def evaluate(self, state: Mapping[str, float]) -> float:
        for variable, (lower, upper) in self.domain.items():
            if variable not in state:
                raise KeyError(f"Missing state variable {variable!r} for energy term {self.name}")
            value = state[variable]
            if lower is not None and value < lower:
                raise ValueError(f"{variable}={value} below domain lower bound {lower}")
            if upper is not None and value > upper:
                raise ValueError(f"{variable}={value} above domain upper bound {upper}")
        result = float(self.evaluator(state))
        if not math.isfinite(result):
            raise ValueError(f"Energy term {self.name} returned a non-finite value")
        return result


@dataclass(frozen=True, slots=True)
class EnergyEvaluation:
    contributions: Mapping[str, float]
    total: float
    unit: str
    exploratory_terms: tuple[str, ...]
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contributions": dict(self.contributions),
            "total": self.total,
            "unit": self.unit,
            "exploratory_terms": list(self.exploratory_terms),
            "assumptions": list(self.assumptions),
        }


class EnergyFunctional:
    """Composable free-energy/objective functional with epistemic separation.

    The class does not claim that arbitrary information scores are physical
    energies. Exploratory terms remain labeled and may be used as optimization
    penalties only when their units and meaning are explicit.
    """

    def __init__(self, terms: Iterable[EnergyTerm] = ()) -> None:
        self._terms: dict[str, EnergyTerm] = {}
        for term in terms:
            self.add(term)

    @property
    def terms(self) -> tuple[EnergyTerm, ...]:
        return tuple(self._terms[name] for name in sorted(self._terms))

    def add(self, term: EnergyTerm) -> None:
        if not term.name.strip():
            raise ValueError("Energy term name cannot be empty")
        if term.name in self._terms:
            raise ValueError(f"Duplicate energy term: {term.name}")
        self._terms[term.name] = term

    def evaluate(self, state: Mapping[str, float]) -> EnergyEvaluation:
        contributions = {term.name: term.evaluate(state) for term in self.terms}
        units = {term.unit for term in self.terms}
        if len(units) > 1:
            raise ValueError(f"Energy terms use incompatible units: {sorted(units)}")
        assumptions = tuple(
            assumption for term in self.terms for assumption in term.assumptions
        )
        return EnergyEvaluation(
            contributions,
            sum(contributions.values()),
            next(iter(units), "J"),
            tuple(term.name for term in self.terms if not term.established),
            assumptions,
        )


def quadratic_elastic_term(
    stiffness_pa: float,
    *,
    strain_variable: str = "strain",
    volume_variable: str = "volume_m3",
) -> EnergyTerm:
    if stiffness_pa <= 0:
        raise ValueError("Stiffness must be positive")
    return EnergyTerm(
        "elastic",
        lambda state: 0.5
        * stiffness_pa
        * state[strain_variable] ** 2
        * state[volume_variable],
        established=True,
        assumptions=("Small-strain scalar elastic approximation.",),
        domain={strain_variable: (None, None), volume_variable: (0.0, None)},
    )


def surface_energy_term(
    surface_energy_j_m2: float,
    *,
    area_variable: str = "surface_area_m2",
) -> EnergyTerm:
    if surface_energy_j_m2 < 0:
        raise ValueError("Surface energy density cannot be negative")
    return EnergyTerm(
        "surface",
        lambda state: surface_energy_j_m2 * state[area_variable],
        established=True,
        assumptions=("Constant isotropic surface energy.",),
        domain={area_variable: (0.0, None)},
    )


def thermal_sensible_term(
    heat_capacity_j_kg_k: float,
    *,
    mass_variable: str = "mass_kg",
    delta_temperature_variable: str = "delta_temperature_k",
) -> EnergyTerm:
    if heat_capacity_j_kg_k <= 0:
        raise ValueError("Heat capacity must be positive")
    return EnergyTerm(
        "thermal_sensible",
        lambda state: heat_capacity_j_kg_k
        * state[mass_variable]
        * state[delta_temperature_variable],
        established=True,
        assumptions=("Constant heat capacity over the temperature interval.",),
        domain={mass_variable: (0.0, None)},
    )


def information_penalty_term(
    coefficient_j: float,
    *,
    complexity_variable: str = "model_complexity",
) -> EnergyTerm:
    if coefficient_j < 0:
        raise ValueError("Penalty coefficient cannot be negative")
    return EnergyTerm(
        "information_penalty",
        lambda state: coefficient_j * state[complexity_variable],
        established=False,
        assumptions=(
            "Optimization penalty only; not a thermodynamic energy without a separate derivation.",
        ),
        domain={complexity_variable: (0.0, None)},
    )
