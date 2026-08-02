from __future__ import annotations

import json

from omega_generator_discovery_t.campaign import (
    CampaignAxes,
    CampaignEmitter,
    CampaignSpec,
    generator_addition,
    iter_generator_bundles,
    mixed_radix_decode,
    partition_campaign,
    stream_digest,
)


def test_default_campaign_exceeds_one_million_logical_records():
    spec = CampaignSpec()

    assert spec.generator_count == 131_072
    assert spec.benchmark_count == 1_048_576
    assert spec.logical_record_count == 1_179_648
    assert spec.records_per_bundle == 9
    assert spec.manifest()["no_permanent_total_addition_cap"] is True


def test_mixed_radix_mapping_is_deterministic_at_both_frontiers():
    spec = CampaignSpec()

    assert mixed_radix_decode(0, spec.axes.radices) == (0, 0, 0, 0, 0)
    assert mixed_radix_decode(spec.generator_count - 1, spec.axes.radices) == (
        31,
        31,
        7,
        3,
        3,
    )
    first = generator_addition(spec, 0)
    last = generator_addition(spec, spec.generator_count - 1)
    assert first["addition_id"] == "GEN-R03-000000000"
    assert last["addition_id"] == "GEN-R03-000131071"
    assert first["addition_id"] != last["addition_id"]


def test_balanced_partitions_cover_campaign_exactly_without_overlap():
    spec = CampaignSpec()
    partitions = partition_campaign(spec, 64)

    assert len(partitions) == 64
    assert partitions[0].generator_start == 0
    assert partitions[-1].generator_stop == spec.generator_count
    assert sum(part.generator_bundles for part in partitions) == spec.generator_count
    assert sum(part.logical_records for part in partitions) == spec.logical_record_count
    assert all(
        left.generator_stop == right.generator_start
        for left, right in zip(partitions, partitions[1:])
    )


def test_streams_more_than_one_hundred_thousand_records_without_materializing():
    spec = CampaignSpec()
    bundle_count = 12_000

    count, digest = stream_digest(
        iter_generator_bundles(spec, start=0, stop=bundle_count)
    )

    assert count == 108_000
    assert len(digest) == 64
    int(digest, 16)


def test_emitter_is_atomic_partitioned_and_resumable(tmp_path):
    spec = CampaignSpec(
        campaign_id="test-campaign",
        axes=CampaignAxes(
            domains=("spectral", "crystal"),
            families=("translation", "rotation"),
            scales=("micro",),
            representations=("operator",),
            evidence_modes=("prediction",),
        ),
        benchmark_variants=3,
    )
    partition = partition_campaign(spec, 1)[0]
    output = tmp_path / "campaign"
    emitter = CampaignEmitter(spec, partition, output, bundles_per_shard=2)

    report = emitter.emit()
    resumed = emitter.emit(resume=True)

    assert report.emitted_generator_bundles == 4
    assert report.emitted_logical_records == 16
    assert report.shards == 2
    assert resumed.emitted_logical_records == 16
    assert resumed.shards == 2
    checkpoint = json.loads((output / "checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["status"] == "completed"
    assert checkpoint["next_generator"] == 4
    shard_lines = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in sorted((output / "records").glob("*.jsonl"))
    )
    assert shard_lines == 16
    assert not list(output.rglob("*.tmp"))
