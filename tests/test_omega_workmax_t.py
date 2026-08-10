from __future__ import annotations

import pytest

from omega_workmax_t import (
    CrystallizationGovernor,
    ProofGates,
    WorkHypergraph,
    WorkPacket,
    WorkTelemetryInput,
    adaptive_worker_sweep,
    build_report,
    compute_metrics,
    decide_promotion,
    deduplicate_packets,
    plan_waves,
    route_capabilities,
    simulate,
)


def packet(work_id: str, **kwargs) -> WorkPacket:
    defaults = dict(objective=work_id, artifact=f"{work_id}.json", estimated_seconds=10.0)
    defaults.update(kwargs)
    return WorkPacket(work_id=work_id, **defaults)


def test_graph_rejects_cycle() -> None:
    with pytest.raises(ValueError, match="acyclic"):
        WorkHypergraph((packet("a", dependencies=("b",)), packet("b", dependencies=("a",))))


def test_semantic_dedup_prefers_stronger_evidence() -> None:
    rows = (
        packet("a", objective="same", artifact="same", semantic_key="same-task", evidence_weight=0.2),
        packet("b", objective="other wording", artifact="other", semantic_key="same-task", evidence_weight=0.9),
    )
    result = deduplicate_packets(rows)
    assert [item.work_id for item in result.unique] == ["b"]
    assert result.duplicate_to_canonical == {"a": "b"}


def test_critical_path_and_blocking_power() -> None:
    graph = WorkHypergraph(
        (
            packet("a", estimated_seconds=2),
            packet("b", dependencies=("a",), estimated_seconds=5),
            packet("c", dependencies=("a",), estimated_seconds=1),
            packet("d", dependencies=("b", "c"), estimated_seconds=3),
        )
    )
    assert graph.critical_path().seconds == 10
    assert graph.critical_path().work_ids == ("a", "b", "d")
    assert graph.blocking_power("a") == 3


def test_wave_planner_preserves_dependencies() -> None:
    graph = WorkHypergraph((packet("a"), packet("b"), packet("c", dependencies=("a", "b"))))
    waves = plan_waves(graph, workers=2)
    assert set(waves[0].work_ids) == {"a", "b"}
    assert waves[1].work_ids == ("c",)


def test_twin_parallelism_respects_structural_lower_bound() -> None:
    graph = WorkHypergraph(
        (
            packet("a", estimated_seconds=10),
            packet("b", estimated_seconds=10),
            packet("c", dependencies=("a",), estimated_seconds=10),
            packet("d", dependencies=("b",), estimated_seconds=10),
        )
    )
    serial = simulate(graph, 1)
    parallel = simulate(graph, 2)
    assert serial.wall_seconds == 40
    assert parallel.wall_seconds == 20
    assert parallel.wall_seconds >= parallel.theoretical_lower_bound_seconds


def test_adaptive_worker_sweep_ends_at_real_packet_count() -> None:
    graph = WorkHypergraph(tuple(packet(f"w{i}") for i in range(7)))
    results = adaptive_worker_sweep(graph)
    assert [item.workers for item in results] == [1, 2, 4, 7]


def test_work_metrics_expose_fanout_and_closure() -> None:
    metrics = compute_metrics(
        WorkTelemetryInput(
            impacted_workunits=2,
            triggered_jobs=20,
            started_artifacts=10,
            crystallized_artifacts=6,
            validated_integrated_artifacts=5,
            maintained_manual_lines=100,
            wall_seconds=50,
            validation_compute_seconds=100,
            evidence_points=25,
            queue_seconds=40,
            obsolete_queue_seconds=10,
            raw_work_units=20,
            duplicate_work_units=4,
            mean_quality=0.9,
        )
    )
    assert metrics.fanout_factor == 10
    assert metrics.closure_ratio == 0.6
    assert metrics.crystallization_debt == 4
    assert metrics.queue_waste_ratio == 0.25


def test_crystallization_governor_switches_modes_by_debt_ratio() -> None:
    governor = CrystallizationGovernor()
    assert governor.decide(started=10, crystallized=9).mode == "EXPAND"
    assert governor.decide(started=10, crystallized=7).mode == "BALANCED"
    assert governor.decide(started=10, crystallized=4).mode == "CRYSTALLIZE"


def test_capability_router_is_reuse_first_but_non_authorizing() -> None:
    work = packet("audit", objective="optimize github actions", artifact="ci report", tags=("github", "actions"))
    records = [
        {
            "capability_id": "omega-actions",
            "canonical_name": "GitHub Actions optimizer",
            "domains": ["github", "actions", "ci"],
            "evidence_weight": 0.9,
            "default_authority": "L3_PLAN",
            "reusable": True,
        }
    ]
    matches = route_capabilities(work, records, reuse_threshold=0.2)
    assert matches[0].decision == "REUSE_CANDIDATE"
    assert matches[0].authority == "L3_PLAN"


def test_promotion_fails_closed_on_proof_gate() -> None:
    baseline = compute_metrics(
        WorkTelemetryInput(1, 3, 2, 1, 1, 10, 10, 10, 1, 2, 1, 2, 0)
    )
    candidate = compute_metrics(
        WorkTelemetryInput(1, 1, 2, 2, 2, 10, 5, 5, 2, 1, 0, 2, 0)
    )
    decision = decide_promotion(
        baseline,
        candidate,
        ProofGates(True, True, True, False, True),
    )
    assert decision.status == "REJECT_PROOF_GATES"
    assert decision.automatic_merge_authorized is False


def test_promotion_can_recommend_human_review_without_auto_merge() -> None:
    baseline = compute_metrics(
        WorkTelemetryInput(1, 8, 10, 5, 5, 100, 100, 100, 5, 50, 25, 10, 2)
    )
    candidate = compute_metrics(
        WorkTelemetryInput(1, 2, 10, 9, 9, 100, 50, 50, 10, 10, 1, 10, 0)
    )
    decision = decide_promotion(
        baseline,
        candidate,
        ProofGates(True, True, True, True, True),
    )
    assert decision.status == "PROMOTE_CANDIDATE_FOR_HUMAN_REVIEW"
    assert decision.automatic_merge_authorized is False


def test_integrated_report_rewires_deduplicated_dependencies() -> None:
    report = build_report(
        {
            "workers": 2,
            "packets": [
                {"work_id": "a", "objective": "A", "artifact": "a", "semantic_key": "same", "evidence_weight": 0.9},
                {"work_id": "a2", "objective": "A clone", "artifact": "a2", "semantic_key": "same", "evidence_weight": 0.2},
                {"work_id": "b", "objective": "B", "artifact": "b", "dependencies": ["a2"]},
            ],
        }
    )
    assert report["unique_packet_count"] == 2
    assert report["duplicate_to_canonical"] == {"a2": "a"}
    assert report["topological_order"] == ["a", "b"]
    assert report["automatic_merge_authorized"] is False
    assert len(report["report_digest"]) == 64
