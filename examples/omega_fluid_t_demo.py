from __future__ import annotations

import json

from omega_fluid_t.dimensionless import DimensionlessInput, compute_dimensionless
from omega_fluid_t.frontier import default_fluid_space
from omega_fluid_t.oak import run_core_benchmarks


def main() -> None:
    water = compute_dimensionless(
        DimensionlessInput(
            density=998.0,
            velocity=1.5,
            length=0.02,
            dynamic_viscosity=1.002e-3,
            sound_speed=1480.0,
            gravity=9.81,
            surface_tension=0.072,
        )
    )
    space = default_fluid_space()
    payload = {
        "dimensionless": water.to_dict(),
        "frontier": space.plan(start=0, count=10_000).to_dict(),
        "first_genome": space.genome(0).to_dict(),
        "oak": run_core_benchmarks().to_dict(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
