from omega_action_ext_t import (
    ActionDNA,
    ActionManifest,
    ApprovalQueue,
    OAKGate,
    ProofLedger,
    RiskTensor,
)


def _sample_action():
    return ActionDNA(
        name="Create draft PR",
        system="github",
        action_type="open_pr",
        public=True,
        touches_ip=True,
        approved=True,
        reversible=True,
        rollback="close_pr",
        risk=RiskTensor(ip=2, reputation=1, irreversibility=1),
    )


def test_manifest_has_hash_and_dry_run():
    manifest = ActionManifest.compile(_sample_action(), OAKGate(), tags=["github", "oak"])
    data = manifest.to_dict()
    assert data["manifest_hash"].startswith("sha256:")
    assert data["dry_run"]["decision"] in {"needs_approval", "allow_auto"}
    assert "github" in data["tags"]


def test_ledger_appends_hash_chain(tmp_path):
    ledger = ProofLedger(tmp_path / "ledger.jsonl")
    first = ledger.append("manifest", {"id": 1})
    second = ledger.append("manifest", {"id": 2})
    assert second.previous_hash == first.record_hash
    assert ledger.latest_hash() == second.record_hash
    assert len(ledger.records()) == 2


def test_approval_queue_stores_manifest(tmp_path):
    manifest = ActionManifest.compile(_sample_action())
    queue = ApprovalQueue(tmp_path / "queue.json")
    item = queue.add_manifest(manifest)
    assert item.manifest_hash.startswith("sha256:")
    assert queue.items()[0].title == "Create draft PR"
