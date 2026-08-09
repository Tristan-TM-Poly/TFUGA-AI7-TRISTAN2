import json
from pathlib import Path

from omega_neuro_t.r06_protocol import protocol_registry


def test_preregistration_ledger_matches_executable_protocol_hashes():
    ledger = json.loads(Path("reports/omega_neuro_r06_preregistration.json").read_text(encoding="utf-8"))
    registry = protocol_registry()
    assert ledger["automatic_biological_promotion"] is False
    assert ledger["status"] == "PROTOCOL_FROZEN_NO_EXTERNAL_BIOLOGICAL_RESULT"
    assert set(ledger["protocols"]) == set(registry)
    for hypothesis_id, item in ledger["protocols"].items():
        assert item["protocol_hash"] == registry[hypothesis_id]["protocol_hash"]
        assert item["protocol_id"] == registry[hypothesis_id]["protocol_id"]
        assert tuple(item["source_priority"]) == tuple(registry[hypothesis_id]["source_priority"])
