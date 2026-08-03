import json
from pathlib import Path

from omega_vla_t.r03.wave2.campaign_cli import main
from omega_vla_t.r03.wave2.campaigns import OperatorCampaignCodec


def test_campaign_codec_is_large_reversible_and_deterministic() -> None:
    codec = OperatorCampaignCodec()
    assert codec.size > 10**12
    assert codec.manifest()["permanent_total_cap"] is None
    indices = tuple(codec.iter_indices(4096, seed=2026))
    assert len(indices) == len(set(indices))
    for index in indices[:128] + indices[-128:]:
        address = codec.decode(index)
        assert codec.encode(address) == index
        assert len(address.digest()) == 64


def test_campaign_plan_resume_offsets_do_not_overlap() -> None:
    codec = OperatorCampaignCodec()
    first = codec.plan(1000, seed=9, start_offset=0)
    second = codec.plan(1000, seed=9, start_offset=1000)
    first_digests = {address.digest() for address in first.addresses}
    second_digests = {address.digest() for address in second.addresses}
    assert first_digests.isdisjoint(second_digests)
    assert first.aggregate_digest != second.aggregate_digest
    assert first.logical_frontier_size == codec.size
    assert first.permanent_total_cap is None
    assert first.theorem_claimed is False


def test_campaign_plan_is_byte_deterministic() -> None:
    codec = OperatorCampaignCodec()
    first = codec.plan(257, seed=17, start_offset=41).to_dict()
    second = codec.plan(257, seed=17, start_offset=41).to_dict()
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_campaign_cli_manifest_decode_plan_and_audit(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    assert main(["manifest", "--output", str(manifest_path)]) == 0
    manifest = json.loads(manifest_path.read_text())
    assert manifest["logical_frontier_size"] > 10**12
    assert manifest["permanent_total_cap"] is None

    decode_path = tmp_path / "decode.json"
    assert main(["decode", "123456789", "--output", str(decode_path)]) == 0
    decoded = json.loads(decode_path.read_text())
    assert decoded["roundtrip_index"] == 123456789

    plan_path = tmp_path / "plan.json"
    assert main(
        [
            "plan",
            "--count",
            "128",
            "--seed",
            "2026",
            "--start-offset",
            "64",
            "--output",
            str(plan_path),
        ]
    ) == 0
    plan = json.loads(plan_path.read_text())
    assert plan["generated"] == 128
    assert plan["start_offset"] == 64
    assert len(plan["addresses"]) == 128

    audit_path = tmp_path / "audit.json"
    assert main(
        [
            "audit-roundtrip",
            "--count",
            "1024",
            "--seed",
            "2026",
            "--output",
            str(audit_path),
        ]
    ) == 0
    audit = json.loads(audit_path.read_text())
    assert audit["passed"] is True
    assert audit["unique_indices"] == 1024
