import json

from omega_pct_t.r03max.campaign import CampaignBudget, CampaignRunner


def test_campaign_deduplicates_and_checkpoints(tmp_path):
    source = ({"id": index % 7, "value": index % 7} for index in range(100))
    runner = CampaignRunner(
        tmp_path,
        CampaignBudget(checkpoint_every=2, shard_target_bytes=120),
    )
    try:
        state = runner.run(source)
    finally:
        runner.close()
    assert state.accepted == 7
    assert state.duplicates == 93
    assert state.shards >= 2
    checkpoint = json.loads((tmp_path / "checkpoint.json").read_text())
    assert checkpoint["stop_reason"] == "source_exhausted"


def test_campaign_stops_on_real_byte_budget(tmp_path):
    source = ({"id": index, "payload": "x" * 100} for index in range(10000))
    runner = CampaignRunner(tmp_path, CampaignBudget(max_output_bytes=1000))
    try:
        state = runner.run(source)
    finally:
        runner.close()
    assert state.stop_reason == "byte_budget"
    assert state.accepted < 10000
