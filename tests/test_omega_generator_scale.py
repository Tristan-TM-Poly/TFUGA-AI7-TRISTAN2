from __future__ import annotations

import json

from omega_generator_discovery_t.campaign import CampaignAxes, CampaignSpec
from omega_generator_discovery_t.campaign_scale import (
    FrontierLedger,
    FrontierObservation,
    ScalePlanner,
    ScalePolicy,
    ValidationPolicy,
    decide_next_frontier,
    iter_epoch_bundles,
    resolve_target_records,
    validate_epoch_range,
    write_partition_matrix,
)
from omega_generator_discovery_t.campaign_scale_emitter import ScalePartitionEmitter


def _tiny_spec() -> CampaignSpec:
    return CampaignSpec(
        campaign_id="scale-test",
        axes=CampaignAxes(
            domains=("spectral", "crystal"),
            families=("translation", "rotation"),
            scales=("micro",),
            representations=("operator",),
            evidence_modes=("prediction",),
        ),
        benchmark_variants=3,
    )


def test_billion_profile_is_a_finite_workload_not_a_permanent_cap():
    spec = CampaignSpec()
    target = resolve_target_records(spec, profile="billion")
    plan = ScalePlanner(spec).plan(target)

    assert target == 1_179_648_000
    assert plan.planned_logical_records == target
    assert plan.epoch_count == 1_000
    assert sum(epoch.logical_records for epoch in plan.epochs) == target
    assert sum(partition.logical_records for partition in plan.partitions) == target
    assert plan.no_permanent_total_addition_cap is True


def test_custom_target_rounds_only_to_atomic_bundle_boundary():
    spec = _tiny_spec()
    plan = ScalePlanner(
        spec,
        ScalePolicy(target_records_per_partition=7, bundles_per_shard=2),
    ).plan(101)

    assert plan.records_per_bundle == 4
    assert plan.planned_logical_records == 104
    assert plan.rounding_overage_records == 3
    assert sum(part.generator_bundles for part in plan.partitions) * 4 == 104
    assert all(part.generator_stop >= part.generator_start for part in plan.partitions)


def test_epoch_ids_links_and_content_are_collision_free():
    spec = _tiny_spec()
    epoch_zero = list(iter_epoch_bundles(spec, 0, start=0, stop=1))
    epoch_one = list(iter_epoch_bundles(spec, 1, start=0, stop=1))

    assert epoch_zero[0]["addition_id"] != epoch_one[0]["addition_id"]
    assert epoch_zero[0]["payload"] != epoch_one[0]["payload"]
    assert epoch_zero[0]["payload"]["benchmark_ids"] == [
        record["addition_id"] for record in epoch_zero[1:]
    ]
    assert all(
        record["payload"]["generator_id"] == epoch_zero[0]["addition_id"]
        for record in epoch_zero[1:]
    )
    assert all(record["metadata"]["epoch_index"] == 0 for record in epoch_zero)


def test_hierarchical_validation_checks_structure_and_all_deep_samples():
    spec = _tiny_spec()
    report = validate_epoch_range(
        spec,
        0,
        policy=ValidationPolicy(sample_ppm=1_000_000),
    )

    assert report.status == "valid"
    assert report.generator_bundles_checked == 4
    assert report.logical_records_checked == 16
    assert report.deep_validations == 4
    assert report.error_count == 0
    assert len(report.sha256) == 64


def test_frontier_controller_expands_or_records_saturation(tmp_path):
    healthy = FrontierObservation(
        requested_logical_records=1_179_648,
        processed_logical_records=1_179_648,
        success=True,
        quality_score=0.999,
        pressure={"memory": 0.30, "ci": 0.20},
        elapsed_seconds=15.0,
    )
    breakthrough = decide_next_frontier(healthy, records_per_bundle=9)
    assert breakthrough.event_type == "M+_breakthrough"
    assert breakthrough.next_requested_records >= 4 * healthy.requested_logical_records
    assert breakthrough.next_requested_records % 9 == 0

    saturated = FrontierObservation(
        requested_logical_records=10_000_000,
        processed_logical_records=6_000_000,
        success=False,
        quality_score=0.92,
        pressure={"memory": 1.20, "api": 0.80},
        elapsed_seconds=120.0,
        notes=("runner exhausted",),
    )
    decision = decide_next_frontier(saturated, records_per_bundle=9)
    ledger = FrontierLedger(tmp_path / "frontier.jsonl")
    ledger.append(breakthrough)
    ledger.append(decision)

    events = [
        json.loads(line)
        for line in (tmp_path / "frontier.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert decision.event_type == "M-_saturation"
    assert "memory" in decision.limiting_dimensions
    assert "quality" in decision.limiting_dimensions
    assert len(events) == 2


def test_scale_emitter_is_atomic_resumable_and_matrix_ready(tmp_path):
    spec = _tiny_spec()
    policy = ScalePolicy(target_records_per_partition=100, bundles_per_shard=2)
    plan = ScalePlanner(spec, policy).plan(spec.logical_record_count)
    partition = plan.partitions[0]
    output = tmp_path / "partition"
    emitter = ScalePartitionEmitter(
        spec,
        partition,
        output,
        bundles_per_shard=2,
    )

    report = emitter.emit()
    resumed = emitter.emit(resume=True)
    matrix_path = tmp_path / "matrix.json"
    write_partition_matrix(plan, matrix_path)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

    assert report.emitted_generator_bundles == 4
    assert report.emitted_logical_records == 16
    assert report.shards == 2
    assert resumed.emitted_logical_records == 16
    assert resumed.shards == 2
    assert matrix["include"][0]["logical_records"] == 16
    assert not list(output.rglob("*.tmp"))
