from __future__ import annotations

import json

from omega_aero_hydro_propulsion_t import (
    OperatingPoint,
    OptimizationConstraints,
    analyze_rotor,
    assess_cavitation,
    default_air,
    default_water,
    demo_rotor,
    grid_optimize,
    run_propulsion_benchmarks,
)


def main() -> None:
    rotor = demo_rotor()
    air_case = analyze_rotor(rotor, default_air(), OperatingPoint(22.0, 2200.0))
    water_case = analyze_rotor(rotor, default_water(), OperatingPoint(3.0, 700.0))
    optimization = grid_optimize(
        rotor,
        default_air(),
        OperatingPoint(22.0, 2200.0),
        diameter_scales=(0.9, 1.0, 1.1),
        chord_scales=(0.9, 1.0),
        pitch_deltas_deg=(-2.0, 0.0, 2.0),
        constraints=OptimizationConstraints(minimum_thrust=1.0),
    )
    print(
        json.dumps(
            {
                "air": air_case.to_dict(),
                "water_cavitation": assess_cavitation(water_case, default_water()).to_dict(),
                "best": None if optimization.best is None else optimization.best.to_dict(),
                "oak": run_propulsion_benchmarks().to_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
