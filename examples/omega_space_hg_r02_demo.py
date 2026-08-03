from __future__ import annotations

import json

from omega_space_hg_t.r02 import (
    run_r02_oak_benchmarks,
    simulate_r02_attitude,
    simulate_r02_orbit,
)

payload = {
    "orbit": simulate_r02_orbit(duration_orbits=3.0, step_s=20.0, include_drag=True, include_srp=True),
    "attitude": simulate_r02_attitude(duration_s=120.0, step_s=0.2, sensor_noise=True),
    "oak": run_r02_oak_benchmarks(),
    "theorem_claimed": False,
    "scientific_validation_claimed": False,
    "flight_qualified_claimed": False,
    "operational_ephemeris_claimed": False,
    "conjunction_assessment_claimed": False,
    "stability_proof_claimed": False,
}
print(json.dumps(payload, indent=2, sort_keys=True))
