"""Deterministic parameter atlases and stroboscopic maps."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Iterator

from .analytic import canonical_parameters
from .integrators import Trajectory, simulate_adaptive
from .model import Invariants, PrincipalMoments, TorqueFunction, principal_axis_stability


@dataclass(frozen=True)
class AtlasConfig:
    i2_values: tuple[float, ...]
    i3_values: tuple[float, ...]
    energy_fractions: tuple[float, ...]
    angular_momentum: float = 1.0

    def __post_init__(self) -> None:
        if not self.i2_values or not self.i3_values or not self.energy_fractions:
            raise ValueError("atlas axes must be non-empty")
        if not isfinite(self.angular_momentum) or self.angular_momentum <= 0.0:
            raise ValueError("angular_momentum must be finite and positive")
        if any(not 1.0 < value for value in self.i2_values):
            raise ValueError("all i2 values must exceed normalized I1=1")
        if any(not isfinite(value) for value in self.i3_values):
            raise ValueError("i3 values must be finite")
        if any(not 0.0 < fraction < 1.0 for fraction in self.energy_fractions):
            raise ValueError("energy fractions must lie strictly inside (0,1)")

    @property
    def logical_cells(self) -> int:
        return len(self.i2_values) * len(self.i3_values) * len(self.energy_fractions)


@dataclass(frozen=True)
class AtlasCell:
    cell_id: str
    i1: float
    i2: float
    i3: float
    energy_fraction: float
    energy: float
    angular_momentum_squared: float
    regime: str
    elliptic_parameter_m: float
    period: float
    stable_axis_1_rate: float
    unstable_axis_2_rate: float
    stable_axis_3_rate: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_atlas_config(
    *,
    inertia_count: int = 8,
    energy_count: int = 32,
    angular_momentum: float = 1.0,
) -> AtlasConfig:
    if inertia_count < 2 or energy_count < 4:
        raise ValueError("inertia_count >= 2 and energy_count >= 4 are required")
    i2_values = tuple(1.1 + 1.8 * index / (inertia_count - 1) for index in range(inertia_count))
    i3_values = tuple(3.1 + 3.9 * index / (inertia_count - 1) for index in range(inertia_count))
    fractions = tuple((index + 1) / (energy_count + 1) for index in range(energy_count))
    return AtlasConfig(i2_values, i3_values, fractions, angular_momentum)


def iter_atlas(config: AtlasConfig) -> Iterator[AtlasCell]:
    l2 = config.angular_momentum * config.angular_momentum
    for i2_index, i2 in enumerate(config.i2_values):
        for i3_index, i3 in enumerate(config.i3_values):
            if not i3 > i2:
                continue
            model = PrincipalMoments(1.0, i2, i3)
            minimum = l2 / (2.0 * i3)
            maximum = l2 / 2.0
            for energy_index, fraction in enumerate(config.energy_fractions):
                energy = minimum + fraction * (maximum - minimum)
                inv = Invariants(energy, l2)
                threshold = l2 / (2.0 * i2)
                if abs(energy - threshold) <= 1e-12:
                    continue
                regime, _, _, _, _, parameter_m, period = canonical_parameters(model, inv)
                cell_id = f"rb-{i2_index:03d}-{i3_index:03d}-{energy_index:04d}"
                yield AtlasCell(
                    cell_id=cell_id,
                    i1=1.0,
                    i2=i2,
                    i3=i3,
                    energy_fraction=fraction,
                    energy=energy,
                    angular_momentum_squared=l2,
                    regime=regime,
                    elliptic_parameter_m=parameter_m,
                    period=period,
                    stable_axis_1_rate=principal_axis_stability(model, 1, 1.0).rate,
                    unstable_axis_2_rate=principal_axis_stability(model, 2, 1.0).rate,
                    stable_axis_3_rate=principal_axis_stability(model, 3, 1.0).rate,
                )


def atlas_manifest(config: AtlasConfig) -> dict[str, object]:
    cells = [cell.to_dict() for cell in iter_atlas(config)]
    canonical = json.dumps(cells, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "omega-rigid-body-atlas-v1",
        "requested_logical_cells": config.logical_cells,
        "materialized_cells": len(cells),
        "sha256": sha256(canonical.encode("utf-8")).hexdigest(),
        "angular_momentum": config.angular_momentum,
        "cells": cells,
        "claims": {
            "physical_certification": False,
            "experimental_validation": False,
            "new_law_of_physics": False,
        },
    }


def stroboscopic_map(
    model: PrincipalMoments,
    omega0,
    *,
    forcing_period: float,
    cycles: int,
    torque: TorqueFunction | None = None,
    damping: float = 0.0,
    rtol: float = 1e-9,
    atol: float = 1e-11,
) -> Trajectory:
    if forcing_period <= 0.0 or not isfinite(forcing_period):
        raise ValueError("forcing_period must be finite and positive")
    if cycles < 1:
        raise ValueError("cycles must be at least 1")
    return simulate_adaptive(
        model,
        omega0,
        t_end=forcing_period * cycles,
        samples=cycles,
        torque=torque,
        damping=damping,
        rtol=rtol,
        atol=atol,
    )
