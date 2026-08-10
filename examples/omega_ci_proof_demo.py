from __future__ import annotations

import json
from pathlib import Path

from omega_ci_proof_t.claims import ClaimRegistry
from omega_ci_proof_t.io import test_catalog_from_mapping
from omega_ci_proof_t.planner import ProofPlanner

ROOT = Path(__file__).parents[1]
registry = ClaimRegistry.from_json(ROOT / "data/omega_ci_proof_t/claims.json")
catalog = test_catalog_from_mapping(json.loads((ROOT / "data/omega_ci_proof_t/tests.json").read_text()))
impact = json.loads((ROOT / "data/omega_ci_proof_t/sample-impact.json").read_text())
plan = ProofPlanner(registry, catalog).plan(impact)
print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
