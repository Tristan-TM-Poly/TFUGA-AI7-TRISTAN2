from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from omega_generator_discovery_t.frontier_store import FrontierStore
from omega_generator_discovery_t.frontier_virtual import (
    AdaptiveWaveScheduler,
    BaseCampaignShape,
    BudgetEnvelope,
    FrontierReceipt,
    LeaseAuthority,
    MerkleMountainRange,
    PromotionEvidence,
    ResourceModel,
    VirtualFrontierPlan,
    VirtualFrontierPolicy,
    evaluate_promotion,
    receipt_chain_valid,
    resolve_frontier_target,
)


SHAPE = BaseCampaignShape(
    campaign_id="omega-generator-discovery-r03-million",
    campaign_fingerprint="f" * 64,
    generator_count=131_072,
    records_per_bundle=9,
)


def make_plan(
    target: int = 1_000_000_000_000,
    *,
    records_per_partition: int = 250_000,
) -> VirtualFrontierPlan:
    return VirtualFrontierPlan.build(
        SHAPE,
        target,
        VirtualFrontierPolicy(
            target_records_per_partition=records_per_partition,
            bundles_per_shard=2_048,
            max_partitions_per_wave=64,
            max_matrix_entries=64,
        ),
    )


def test_trillion_plan_is_analytical_and_exactly_addressable():
    plan = make_plan()

    assert plan.requested_logical_records == 1_000_000_000_000
    assert plan.planned_logical_records % SHAPE.records_per_bundle == 0
    assert plan.planned_logical_records >= plan.requested_logical_records
    assert plan.rounding_overage_records < SHAPE.records_per_bundle
    assert plan.epoch_count > 800_000
    assert plan.total_partition_count > plan.epoch_count
    assert not hasattr(plan, "epochs")
    assert not hasattr(plan, "partitions")
    assert len(plan.plan_fingerprint) == 64


def test_quadrillion_profile_resolves_without_becoming_a_cap():
    target = resolve_frontier_target(profile="quadrillion")
    plan = make_plan(target)

    assert target == 1_000_000_000_000_000
    assert plan.no_permanent_total_addition_cap is True
    assert plan.epoch_count > 800_000_000
    assert plan.to_dict()["oak_boundary"].startswith("Virtual cardinality")


def test_partition_mapping_covers_full_epoch_boundary_and_tail():
    plan = make_plan(2 * SHAPE.logical_records_per_epoch + 123_456)
    first = plan.partition_at(0)
    before_boundary = plan.partition_at(plan.full_epoch_partition_count - 1)
    after_boundary = plan.partition_at(plan.full_epoch_partition_count)
    last = plan.partition_at(plan.total_partition_count - 1)

    assert first.epoch_index == 0
    assert first.generator_start == 0
    assert before_boundary.epoch_index == 0
    assert before_boundary.generator_stop == SHAPE.generator_count
    assert after_boundary.epoch_index == 1
    assert after_boundary.generator_start == 0
    assert last.epoch_index == plan.epoch_count - 1
    assert last.generator_stop == plan.tail_generator_bundles
    assert len({value.partition_key for value in (first, before_boundary, after_boundary, last)}) == 4


def test_high_cursor_partition_page_is_bounded():
    plan = make_plan()
    cursor = plan.total_partition_count - 17
    page = plan.partition_page(cursor=cursor, limit=10_000)

    assert page["count"] == 17
    assert page["next_cursor"] == plan.total_partition_count
    assert page["complete"] is True
    assert page["include"][0]["global_partition_index"] == cursor
    assert page["include"][-1]["global_partition_index"] == plan.total_partition_count - 1


def test_epoch_page_can_jump_to_extreme_index():
    plan = make_plan(resolve_frontier_target(profile="quadrillion"))
    cursor = plan.epoch_count - 3
    page = plan.epoch_page(cursor, limit=50)

    assert page["count"] == 3
    assert page["complete"] is True
    assert page["epochs"][0]["epoch_index"] == cursor
    assert page["epochs"][-1]["epoch_index"] == plan.epoch_count - 1


def test_adaptive_scheduler_obeys_every_budget_dimension():
    plan = make_plan(10_000_000)
    model = ResourceModel(
        bytes_per_record=10,
        nanoseconds_per_record=100,
        cost_microunits_per_record=2,
        records_per_api_call=100_000,
        records_per_file=100_000,
        records_per_commit=1_000_000,
    )
    first = plan.partition_at(0)
    budget = BudgetEnvelope(
        max_logical_records=first.logical_records * 2,
        max_bytes_written=first.logical_records * 20,
        max_nanoseconds=first.logical_records * 200,
        max_cost_microunits=first.logical_records * 4,
        max_api_calls=10,
        max_files=10,
        max_commits=10,
    )
    wave = AdaptiveWaveScheduler(model, max_partitions_per_wave=64).schedule(
        plan, 0, budget
    )

    assert wave.status == "scheduled"
    assert 1 <= wave.partition_count <= 2
    assert budget.fits(wave.usage)
    assert wave.next_cursor == wave.partition_count


def test_scheduler_blocks_when_one_partition_does_not_fit():
    plan = make_plan(1_000_000)
    model = ResourceModel()
    budget = BudgetEnvelope(
        max_logical_records=1,
        max_bytes_written=1,
        max_nanoseconds=1,
        max_cost_microunits=1,
        max_api_calls=1,
        max_files=1,
        max_commits=1,
    )
    wave = AdaptiveWaveScheduler(model).schedule(plan, 0, budget)

    assert wave.status == "blocked"
    assert wave.partition_count == 0
    assert wave.next_cursor == 0
    assert "logical_records" in wave.limiting_dimensions


def test_mmr_is_streaming_deterministic_and_order_sensitive():
    left = MerkleMountainRange()
    right = MerkleMountainRange()
    reversed_mmr = MerkleMountainRange()

    for index in range(10_000):
        record = {"id": index, "payload": f"value-{index}"}
        left.append(record)
        right.append(record)
    for index in reversed(range(10_000)):
        reversed_mmr.append({"id": index, "payload": f"value-{index}"})

    assert left.leaf_count == 10_000
    assert left.root == right.root
    assert left.root != reversed_mmr.root
    assert left.receipt()["peak_count"] <= 14


def test_stateless_lease_signature_and_expiry():
    authority = LeaseAuthority(b"0123456789abcdef0123456789abcdef")
    now = datetime(2026, 8, 2, 19, 0, tzinfo=timezone.utc)
    lease = authority.issue(
        "plan", "partition", "worker", ttl_seconds=60, now=now
    )

    assert authority.verify(lease, now=now + timedelta(seconds=59))
    assert not authority.verify(lease, now=now + timedelta(seconds=60))
    tampered = lease.to_dict()
    tampered["worker_id"] = "attacker"
    assert not authority.verify(tampered, now=now)


def test_oak_gate_blocks_volume_only_and_promotes_complete_synthetic():
    blocked = evaluate_promotion("validated_synthetic", PromotionEvidence())
    allowed = evaluate_promotion(
        "validated_synthetic",
        PromotionEvidence(
            structural_validation=True,
            deterministic_reproduction=True,
            provenance_complete=True,
            negative_controls=True,
            baseline_comparison=True,
            uncertainty_quantified=True,
        ),
    )

    assert blocked.status == "block"
    assert "negative_controls" in blocked.missing_requirements
    assert allowed.status == "promote"
    assert allowed.missing_requirements == ()
    assert "never substitute" in allowed.warning


def test_empirical_and_canon_require_real_world_evidence():
    synthetic = PromotionEvidence(
        structural_validation=True,
        deterministic_reproduction=True,
        provenance_complete=True,
        negative_controls=True,
        baseline_comparison=True,
        uncertainty_quantified=True,
    )
    empirical = evaluate_promotion("empirical", synthetic)
    canon = evaluate_promotion("canon", synthetic)

    assert empirical.status == "block"
    assert {"real_data", "safety_review"} <= set(empirical.missing_requirements)
    assert canon.status == "block"
    assert "independent_review" in canon.missing_requirements


def test_receipt_chain_detects_tampering():
    mmr = MerkleMountainRange()
    for index in range(9):
        mmr.append(f"record-{index}")
    first = FrontierReceipt.create(
        plan_fingerprint="plan",
        partition_key="p0",
        worker_id="w",
        logical_records=9,
        generator_bundles=1,
        mmr_root=mmr.root,
        leaf_count=mmr.leaf_count,
        validation_status="valid",
        completed_at=datetime(2026, 8, 2, 19, 0, tzinfo=timezone.utc),
    )
    second = FrontierReceipt.create(
        plan_fingerprint="plan",
        partition_key="p1",
        worker_id="w",
        logical_records=9,
        generator_bundles=1,
        mmr_root=mmr.root,
        leaf_count=mmr.leaf_count,
        validation_status="valid",
        previous_receipt_hash=first.receipt_hash,
        completed_at=datetime(2026, 8, 2, 19, 1, tzinfo=timezone.utc),
    )

    assert receipt_chain_valid((first, second))
    tampered = FrontierReceipt(**{**second.to_dict(), "logical_records": 10})
    assert not receipt_chain_valid((first, tampered))


def test_sqlite_store_claim_complete_dedup_and_audit(tmp_path):
    plan = make_plan(1_000_000, records_per_partition=250_000)
    store = FrontierStore(tmp_path / "frontier.sqlite3")
    seeded = store.seed_partition_page(plan, cursor=0, limit=3)

    assert seeded == 3
    claim = store.claim(plan.plan_fingerprint, "worker-1", ttl_seconds=60)
    assert claim is not None
    assert claim["global_partition_index"] == 0

    mmr = MerkleMountainRange()
    for index in range(claim["logical_records"]):
        mmr.append(f"{claim['partition_key']}:{index}")
    partition = plan.partition_at(claim["global_partition_index"])
    receipt = FrontierReceipt.create(
        plan_fingerprint=plan.plan_fingerprint,
        partition_key=claim["partition_key"],
        worker_id="worker-1",
        logical_records=claim["logical_records"],
        generator_bundles=partition.generator_bundles,
        mmr_root=mmr.root,
        leaf_count=mmr.leaf_count,
        validation_status="valid",
    )

    assert store.complete(claim["lease_token"], receipt)
    assert not store.complete(claim["lease_token"], receipt)
    assert store.register_exact_fingerprint(
        "a" * 64,
        namespace="test",
        kind="record",
        first_partition_key=claim["partition_key"],
        payload_bytes=123,
    )
    assert not store.register_exact_fingerprint(
        "a" * 64,
        namespace="test",
        kind="record",
        first_partition_key=claim["partition_key"],
        payload_bytes=123,
    )
    status = store.status(plan.plan_fingerprint)
    audit = store.integrity_audit(plan.plan_fingerprint)

    assert status["partition_status"]["completed"] == 1
    assert status["partition_status"]["pending"] == 2
    assert status["receipt_count"] == 1
    assert audit["status"] == "valid"
    assert audit["partitions_audited"] == 3


def test_store_expired_lease_is_reclaimed(tmp_path):
    plan = make_plan(1_000_000)
    store = FrontierStore(tmp_path / "frontier.sqlite3")
    store.seed_partition_page(plan, limit=1)
    now = datetime(2026, 8, 2, 19, 0, tzinfo=timezone.utc)
    first = store.claim(
        plan.plan_fingerprint, "worker-old", ttl_seconds=10, now=now
    )
    second = store.claim(
        plan.plan_fingerprint,
        "worker-new",
        ttl_seconds=10,
        now=now + timedelta(seconds=11),
    )

    assert first is not None and second is not None
    assert first["partition_key"] == second["partition_key"]
    assert first["lease_token"] != second["lease_token"]
    assert second["worker_id"] == "worker-new"


def test_store_rejects_receipt_for_wrong_lease(tmp_path):
    plan = make_plan(1_000_000)
    store = FrontierStore(tmp_path / "frontier.sqlite3")
    store.seed_partition_page(plan, limit=1)
    claim = store.claim(plan.plan_fingerprint, "worker")
    assert claim is not None

    receipt = FrontierReceipt.create(
        plan_fingerprint=plan.plan_fingerprint,
        partition_key="wrong",
        worker_id="worker",
        logical_records=claim["logical_records"],
        generator_bundles=1,
        mmr_root="0" * 64,
        leaf_count=1,
        validation_status="valid",
    )
    with pytest.raises(ValueError, match="does not match"):
        store.complete(claim["lease_token"], receipt)
