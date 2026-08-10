from __future__ import annotations

from omega_game.engines.integrated_oakbench import (
    IntegratedOAKBenchConfig,
    run_integrated_oakbench,
)


def _small_config(seed: int = 1401) -> IntegratedOAKBenchConfig:
    return IntegratedOAKBenchConfig(
        seed=seed,
        max_steps=5,
        layout_count=3,
        campaign_shards=2,
        process_workers=2,
        fairness_threshold=0.50,
    )


def test_integrated_oakbench_accepts_only_when_all_invariants_and_faults_pass() -> None:
    report = run_integrated_oakbench(_small_config())
    assert report.accepted
    assert report.invariant_checks
    assert all(report.invariant_checks.values())
    assert report.fault_matrix
    assert all(row.detected for row in report.fault_matrix)
    assert len(report.deterministic_receipt) == 64


def test_integrated_oakbench_deterministic_receipt_repeats_across_runs() -> None:
    config = _small_config()
    first = run_integrated_oakbench(config)
    second = run_integrated_oakbench(config)
    assert first.accepted and second.accepted
    assert first.deterministic_payload() == second.deterministic_payload()
    assert first.deterministic_receipt == second.deterministic_receipt


def test_empirical_timings_and_speedup_are_excluded_from_deterministic_payload() -> None:
    report = run_integrated_oakbench(_small_config())
    payload = report.deterministic_payload()
    assert "empirical_timings_seconds" not in payload
    assert "observed_process_speedup" not in payload
    assert "deterministic_receipt" not in payload
    assert report.empirical_timings_seconds
    assert all(value >= 0 for value in report.empirical_timings_seconds.values())
    if report.observed_process_speedup is not None:
        assert report.observed_process_speedup >= 0


def test_integrated_oakbench_key_receipts_are_present_and_sha_sized() -> None:
    report = run_integrated_oakbench(_small_config())
    required = {
        "layout_hash",
        "match_replay_hash",
        "map_generalization_receipt",
        "campaign_plan_receipt",
        "campaign_checkpoint_receipt",
        "bundle_receipt",
        "bundle_artifact_sha256",
        "coordinator_head_receipt",
        "experiment_graph_receipt",
        "selection_decision_receipt",
    }
    assert required.issubset(report.receipts)
    for key in required:
        assert len(report.receipts[key]) == 64, key


def test_fault_matrix_covers_major_evidence_boundaries() -> None:
    report = run_integrated_oakbench(_small_config())
    faults = {row.fault_id: row for row in report.fault_matrix}
    required = {
        "replay_hash_tamper",
        "disconnected_layout",
        "checkpoint_result_tamper",
        "bundle_manifest_tamper",
        "cas_content_tamper",
        "coordinator_event_tamper",
        "selection_missing_evidence",
        "held_out_layout_leakage",
        "wrong_worker_ack",
    }
    assert required.issubset(faults)
    assert all(faults[name].detected for name in required)


def test_capability_matrix_distinguishes_local_demonstration_from_unproved_claims() -> None:
    report = run_integrated_oakbench(_small_config())
    by_capability = {row.capability: row for row in report.capabilities}
    demonstrated = [row for row in report.capabilities if row.status == "demonstrated_local"]
    not_demonstrated = [row for row in report.capabilities if row.status == "not_demonstrated"]
    assert len(demonstrated) >= 13
    assert not_demonstrated
    for label in (
        "distributed consensus",
        "remote durable artifact storage",
        "guaranteed multi-process speedup",
        "strategic fairness / fun / general intelligence",
    ):
        assert by_capability[label].status == "not_demonstrated"
        assert by_capability[label].boundary


def test_changing_seed_changes_deterministic_benchmark_identity() -> None:
    first = run_integrated_oakbench(_small_config(seed=1401))
    second = run_integrated_oakbench(_small_config(seed=1402))
    assert first.accepted and second.accepted
    assert first.deterministic_receipt != second.deterministic_receipt


def test_invalid_integrated_oakbench_configuration_fails_closed() -> None:
    bad = IntegratedOAKBenchConfig(layout_count=2)
    try:
        run_integrated_oakbench(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("layout_count < 3 should fail closed")
