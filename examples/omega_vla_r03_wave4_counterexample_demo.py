from __future__ import annotations

import json

from omega_vla_t.r03.wave4 import CounterexampleFrontier, execute_builtin_campaign, run_oakbench

payload = {
    "frontier": CounterexampleFrontier().manifest(),
    "counterexample": execute_builtin_campaign(
        "unconditional_commutativity",
        dimension=2,
        scalar_system="real",
        family="dense",
        seed=2026,
        trials=8,
    ),
    "oak": run_oakbench(),
    "theorem_claimed": False,
    "formal_proof_claimed": False,
    "scientific_validation_claimed": False,
}
print(json.dumps(payload, indent=2, sort_keys=True))
