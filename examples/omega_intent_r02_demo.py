from __future__ import annotations

import json
from pathlib import Path
import tempfile

from omega_intent_t.r02 import AdaptiveBudgetController, CampaignRunner, IntentLedger, synthetic_records
from omega_intent_t.r02.campaign import deterministic_executor
from omega_intent_t.r02.models import BudgetPolicy


with tempfile.TemporaryDirectory(prefix="omega-intent-r02-demo-") as directory:
    ledger_path = Path(directory) / "ledger.sqlite3"
    with IntentLedger(ledger_path) as ledger:
        intent_id = ledger.ingest_intent(
            {
                "id": "INTENT-R02-DEMO",
                "objective": "Compile and execute a finite, resumable intent campaign.",
            }
        )
        controller = AdaptiveBudgetController(
            BudgetPolicy(initial_items=32, initial_bytes=512_000)
        )
        report = CampaignRunner(ledger, controller=controller).run(
            intent_id,
            synthetic_records(intent_id, 2048),
            deterministic_executor,
        )
        payload = {
            "campaign": report.to_dict(),
            "ledger": ledger.summary(intent_id),
            "budget": controller.manifest(),
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "remote_mutations": 0,
            "automatic_merge": False,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
