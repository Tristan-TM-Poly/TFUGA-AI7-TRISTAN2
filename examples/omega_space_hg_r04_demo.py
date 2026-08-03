from __future__ import annotations

import json

from omega_space_hg_t.r04 import (
    canonical_fault_tree,
    run_r04_oak_benchmarks,
    simulate_fdir_scenario,
    simulate_r04_campaign,
)

payload = {
    "independent_fault_tree_probability": canonical_fault_tree().probability(),
    "campaign": simulate_r04_campaign(duration_days=365.25, count=2048),
    "fdir": simulate_fdir_scenario(),
    "oak": run_r04_oak_benchmarks(),
    "theorem_claimed": False,
    "scientific_validation_claimed": False,
    "flight_qualified_claimed": False,
    "operational_reliability_claimed": False,
    "safety_certification_claimed": False,
    "autonomous_safety_claimed": False,
}
print(json.dumps(payload, indent=2, sort_keys=True))
