from __future__ import annotations

import json

from omega_space_hg_t.r05 import (
    run_r05_oak_benchmarks,
    simulate_r05_constellation,
)

payload = {
    "nominal": simulate_r05_constellation(duration_hours=12.0, step_s=120.0),
    "degraded": simulate_r05_constellation(
        duration_hours=12.0,
        step_s=120.0,
        failed_satellites=("sat-p00-s00", "sat-p01-s00", "sat-p02-s00"),
    ),
    "oak": run_r05_oak_benchmarks(),
    "theorem_claimed": False,
    "scientific_validation_claimed": False,
    "flight_qualified_claimed": False,
    "operational_coverage_claimed": False,
    "collision_safety_claimed": False,
    "autonomous_servicing_claimed": False,
}
print(json.dumps(payload, indent=2, sort_keys=True))
