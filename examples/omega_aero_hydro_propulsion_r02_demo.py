from __future__ import annotations

import json

from omega_aero_hydro_propulsion_t import (
    BladeStation,
    OperatingPoint,
    PolarRegistry,
    RotorDesign,
    analyze_annular_bem,
    default_air,
    demo_air_mission,
    demo_polar_table,
    demo_rotor,
    evaluate_mission,
    run_r02_benchmarks,
)


def main() -> None:
    base = demo_rotor()
    registry = PolarRegistry([demo_polar_table()])
    tabulated_design = RotorDesign(
        name="r02-tabulated-demo",
        blade_count=base.blade_count,
        hub_radius=base.hub_radius,
        tip_radius=base.tip_radius,
        stations=tuple(
            BladeStation(station.radius, station.chord, station.twist_deg, "demo-tabulated-symmetric")
            for station in base.stations
        ),
    )
    annular = analyze_annular_bem(
        tabulated_design,
        default_air(),
        OperatingPoint(22.0, 2_200.0),
        registry=registry,
    )
    mission = evaluate_mission(base, default_air(), demo_air_mission())
    payload = {
        "annular": annular.to_dict(),
        "mission": mission.to_dict(),
        "oak": run_r02_benchmarks().to_dict(),
        "status": "research screening; not flight or marine certification",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
