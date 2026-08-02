import json
from omega_re_t.r03_cli import main as cli_main
from omega_re_t.r03_frontier import PERTURBATIONS, build_seeds, iter_cases, manifest, materialize, validate_frontier
from omega_re_t.sharding import CampaignCheckpoint, ShardPlan, ShardReceipt, canonical_digest, iter_pending_shards, merkle_root, verify_receipt_chain


def test_sharding_and_receipts():
    plan = ShardPlan.build("c", 10, 4)
    assert plan.shard_count == 3
    receipts = []
    previous = "0" * 64
    for index in range(plan.shard_count):
        start, stop = plan.bounds(index)
        digests = [canonical_digest({"i": item}) for item in range(start, stop)]
        receipt = ShardReceipt.create(plan, index, digests, previous_receipt_digest=previous)
        receipts.append(receipt)
        previous = receipt.receipt_digest
    assert verify_receipt_chain(plan, receipts)
    checkpoint = CampaignCheckpoint.from_receipts(plan, receipts)
    assert checkpoint.processed_items == 10
    assert tuple(iter_pending_shards(plan, (0, 2))) == (1,)
    assert len(merkle_root(["a", "b"])) == 64


def test_re64_re1024_structure():
    seeds = build_seeds()
    assert len(seeds) == 64
    cases = list(iter_cases())
    assert len(cases) == 1024
    validation = validate_frontier(cases)
    assert validation["valid"]
    report = manifest(cases)
    assert report["seed_count"] == 64
    assert report["perturbation_count"] == len(PERTURBATIONS) == 16
    assert report["claims"]["executed_cases"] == 0
    assert report["claims"]["scientifically_verified_cases"] == 0


def test_materialization_is_deterministic(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    manifest_a = materialize(first)
    manifest_b = materialize(second)
    assert manifest_a == manifest_b
    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text())
    assert len(payload["cases"]) == 1024
    assert len(first.read_text().splitlines()) > 70_000


def test_cli_commands(tmp_path):
    for command in ("catalog", "learn-demo", "grammar-demo", "protocol-demo", "causal-demo", "cleanroom-demo", "genealogy-demo"):
        output = tmp_path / f"{command}.json"
        assert cli_main([command, "--output", str(output)]) == 0
        assert json.loads(output.read_text())
    output = tmp_path / "frontier.json"
    snapshot = tmp_path / "re1024.json"
    assert cli_main(["frontier", "--materialize", str(snapshot), "--shard-size", "128", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["shard_plan"]["shard_count"] == 8
    assert snapshot.exists()
