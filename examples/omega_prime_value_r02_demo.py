from __future__ import annotations

import json
import tempfile
from pathlib import Path

from omega_prime_value_t.r02.engine import CampaignEngine
from omega_prime_value_t.r02.planner import CampaignPlanner, PlannerPolicy
from omega_prime_value_t.r02.storage import CampaignStore


if __name__ == "__main__":
    manifest = CampaignPlanner(
        PlannerPolicy(exponent_min=8, exponent_max=10, k_max=127, shard_size=16)
    ).build()
    with tempfile.TemporaryDirectory(prefix="omega-prime-demo-") as directory:
        with CampaignStore(Path(directory) / "campaign.sqlite3") as store:
            first = CampaignEngine(store).execute(manifest, max_tasks=25)
            second = CampaignEngine(store).execute(manifest)
            print(json.dumps({"first": first.to_dict(), "second": second.to_dict()}, indent=2, sort_keys=True))
