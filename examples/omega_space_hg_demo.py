from __future__ import annotations

import json

from omega_space_hg_t import canonical_6u_mission, optimize_designs, run_oak_benchmarks, simulate_mission


mission = canonical_6u_mission(duration_orbits=0.5, step_s=30.0)
result = simulate_mission(mission)
optimization = optimize_designs(mission, start_offset=0, count=12)

payload = {
    "mission_id": mission.mission_id,
    "metrics": result.metrics.to_dict(),
    "hypergraph": {
        "node_count": result.hypergraph["validation"]["node_count"],
        "edge_count": result.hypergraph["validation"]["edge_count"],
        "sha256": result.hypergraph["sha256"],
    },
    "optimization": {
        "evaluated_count": optimization["frontier"]["evaluated_count"],
        "pareto_count": optimization["pareto_count"],
        "next_offset": optimization["frontier"]["next_offset"],
        "permanent_total_cap": optimization["frontier"]["permanent_total_cap"],
    },
    "oak": run_oak_benchmarks(),
    "theorem_claimed": False,
    "flight_qualified_claimed": False,
    "scientific_validation_claimed": False,
}

print(json.dumps(payload, indent=2, sort_keys=True))
