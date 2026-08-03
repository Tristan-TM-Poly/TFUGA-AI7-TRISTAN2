from __future__ import annotations

import json

from omega_space_hg_t.r03 import run_r03_oak_benchmarks, simulate_r03_networks

payload = {
    "network_simulation": simulate_r03_networks(duration_orbits=8.0, step_s=20.0),
    "oak": run_r03_oak_benchmarks(),
    "theorem_claimed": False,
    "scientific_validation_claimed": False,
    "flight_qualified_claimed": False,
    "operational_network_claimed": False,
    "regulatory_approval_claimed": False,
}
print(json.dumps(payload, indent=2, sort_keys=True))
