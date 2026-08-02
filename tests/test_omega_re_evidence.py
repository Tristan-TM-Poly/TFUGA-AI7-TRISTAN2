from dataclasses import replace

from omega_re_t.evidence import EvidenceLedger
from omega_re_t.models import ClaimStatus


def build_ledger():
    ledger = EvidenceLedger.empty()
    ledger.append(
        record_id="scope-1",
        kind="scope",
        payload={"authorized": True},
        claim_status=ClaimStatus.OBSERVED,
    )
    ledger.append(
        record_id="obs-1",
        kind="observation",
        payload={"input": "A", "output": "0"},
        claim_status=ClaimStatus.MEASURED,
        provenance=("scope-1",),
    )
    return ledger


def test_evidence_chain_round_trip():
    ledger = build_ledger()
    valid, errors = ledger.verify()
    assert valid
    assert errors == ()
    restored = EvidenceLedger.from_jsonl(ledger.to_jsonl())
    assert restored.root_hash == ledger.root_hash
    assert restored.verify() == (True, ())


def test_evidence_chain_detects_tampering():
    ledger = build_ledger()
    ledger.records[1] = replace(ledger.records[1], payload={"input": "A", "output": "1"})
    valid, errors = ledger.verify()
    assert not valid
    assert any("record_hash mismatch" in error for error in errors)


def test_evidence_chain_rejects_duplicate_ids():
    ledger = build_ledger()
    try:
        ledger.append(
            record_id="obs-1",
            kind="observation",
            payload={},
            claim_status=ClaimStatus.OBSERVED,
        )
    except ValueError as error:
        assert "Duplicate" in str(error)
    else:
        raise AssertionError("Expected duplicate record rejection")
