from __future__ import annotations

from omega_code_dojo_t.r02.benchmark import (
    blocked_provenance,
    fixture_provenance,
    run_r02_benchmark,
)
from omega_code_dojo_t.r02.campaign import CampaignEngine
from omega_code_dojo_t.r02.frontier import DEFAULT_FRONTIER
from omega_code_dojo_t.r02.models import CampaignPolicy, StopReason
from omega_code_dojo_t.r02.provenance import IPGate
from omega_code_dojo_t.r02.task_ir import TaskIRCompiler


def test_logical_frontier_cardinality_and_round_trip() -> None:
    assert DEFAULT_FRONTIER.logical_cell_count == 3_221_225_472
    ordinals = (0, 1, 31, 32, 65_537, DEFAULT_FRONTIER.logical_cell_count - 1)
    for ordinal in ordinals:
        cell = DEFAULT_FRONTIER.cell_at(ordinal)
        assert DEFAULT_FRONTIER.ordinal_of(cell) == ordinal


def test_frontier_can_expand_without_rewriting_materialized_cells() -> None:
    expanded = DEFAULT_FRONTIER.extended({"domains": ("quantum_algorithms",)})
    assert expanded.logical_cell_count > DEFAULT_FRONTIER.logical_cell_count
    assert expanded.cell_at(0) == DEFAULT_FRONTIER.cell_at(0)


def test_task_ir_is_deterministic_and_valid() -> None:
    cell = DEFAULT_FRONTIER.cell_at(42)
    compiler = TaskIRCompiler()
    first = compiler.compile(cell, fixture_provenance(), 42)
    second = compiler.compile(cell, fixture_provenance(), 42)
    assert first.to_dict() == second.to_dict()
    assert compiler.validate(first) == ()
    assert compiler.digest(first) == compiler.digest(second)


def test_ip_gate_blocks_restricted_scrape_fixture() -> None:
    result = IPGate().evaluate(blocked_provenance(), "train")
    assert result.decision.value == "block"
    receipt = CampaignEngine().run(CampaignPolicy(4), blocked_provenance())
    assert receipt.materialized_cells == 0
    assert receipt.stop_reason is StopReason.SAFETY_GATE


def test_campaign_has_local_budget_but_no_permanent_cap() -> None:
    receipt = CampaignEngine().run(CampaignPolicy(7), fixture_provenance())
    assert receipt.materialized_cells == 7
    assert receipt.permanent_total_cap is None
    assert receipt.logical_frontier_cells == 3_221_225_472
    assert len(receipt.receipt_sha256) == 64


def test_explicit_permanent_cap_is_honored_when_requested() -> None:
    receipt = CampaignEngine().run(
        CampaignPolicy(materialization_budget=9, permanent_cap=3),
        fixture_provenance(),
    )
    assert receipt.materialized_cells == 3
    assert receipt.stop_reason is StopReason.COST_GATE


def test_benchmark_is_deterministic_and_oak_certified() -> None:
    first = run_r02_benchmark(24)
    second = run_r02_benchmark(24)
    assert first == second
    assert first["status"] == "CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"
    assert first["logical_frontier_cells"] == 3_221_225_472
    assert first["materialized_cells"] == 24
    assert first["permanent_total_cap"] is None
    assert first["pass_rate"] == 1.0
    assert first["mean_mutation_score"] == 1.0
    assert all(first["invariants"].values())


def test_receipt_hash_verification_detects_tampering() -> None:
    from omega_code_dojo_t.r02.receipts import verify_receipt, verify_receipt_dict

    receipt = CampaignEngine().run(CampaignPolicy(5), fixture_provenance())
    assert verify_receipt(receipt)
    payload = receipt.to_dict()
    assert verify_receipt_dict(payload)
    payload["allocated_units"] = int(payload["allocated_units"]) + 1
    assert not verify_receipt_dict(payload)


def test_scheduler_builds_resumable_finite_shards() -> None:
    from omega_code_dojo_t.r02.scheduler import HierarchicalScheduler

    scheduler = HierarchicalScheduler()
    shards = scheduler.plan(
        campaign_id="campaign-test",
        start_ordinal=100,
        materialization_budget=23,
        shard_size=8,
        runner_classes=("standard", "memory"),
    )
    assert [shard.budget for shard in shards] == [8, 8, 7]
    assert sum(shard.budget for shard in shards) == 23
    assert scheduler.resume_ordinal(shards) == 123


def test_memory_genomes_deduplicate_and_count_recurrence() -> None:
    from omega_code_dojo_t.r02.memory import NegativeMemory, PositiveMemory

    negative = NegativeMemory()
    first = negative.record(
        task_id="task-1",
        symptom="wrong answer",
        minimal_counterexample="[]",
        root_cause="missing empty case",
        false_assumption="input is non-empty",
        mutation_operator="empty_case_delete",
        repair="add identity case",
        regression_test="assert solve([]) == 0",
        tags=("arrays", "boundary"),
    )
    second = negative.record(
        task_id="task-1",
        symptom="wrong answer",
        minimal_counterexample="[]",
        root_cause="missing empty case",
        false_assumption="input is non-empty",
        mutation_operator="empty_case_delete",
        repair="add identity case",
        regression_test="assert solve([]) == 0",
        tags=("arrays", "boundary"),
    )
    assert first.failure_id == second.failure_id
    assert second.recurrence_count == 2
    assert len(negative.related("boundary")) == 1

    positive = PositiveMemory()
    strategy = positive.record(
        name="sliding-window",
        preconditions=("contiguous interval",),
        invariant="window state matches current interval",
        decomposition=("expand", "repair", "record"),
        data_structures=("counter",),
        claimed_complexity="O(n)",
        failure_boundary=("non-local dependency",),
        transferable_to=("strings", "streams"),
        proof_sketch="Each endpoint advances monotonically.",
    )
    assert strategy.evidence_count == 1
    assert positive.to_dict()["count"] == 1


def test_oracle_mesh_combines_exact_and_property_checks() -> None:
    from omega_code_dojo_t.r02.oracles import (
        ExactCase,
        ExactOracle,
        OracleMesh,
        PropertyCheck,
        PropertyOracle,
    )

    candidate = lambda values: sum(values)
    mesh = OracleMesh(
        (
            ExactOracle((ExactCase(([1, 2, 3],), 6, "basic"),)),
            PropertyOracle(
                (
                    PropertyCheck("empty identity", lambda fn: fn([]) == 0),
                    PropertyCheck(
                        "permutation invariant",
                        lambda fn: fn([3, 1, 2]) == fn([1, 2, 3]),
                    ),
                )
            ),
        )
    )
    result = mesh.evaluate(candidate)
    assert result.passed
    assert result.checks == 3


def test_dataset_compiler_preserves_license_and_provenance() -> None:
    from omega_code_dojo_t.r02.dataset import DatasetCompiler

    compiler = TaskIRCompiler()
    tasks = tuple(
        compiler.compile(DEFAULT_FRONTIER.cell_at(index), fixture_provenance(), index)
        for index in range(3)
    )
    manifest = DatasetCompiler().compile_task_ir(tasks, "critique")
    assert manifest.record_count == 3
    assert manifest.licenses == ("MIT",)
    assert manifest.training_allowed
    assert len(manifest.records_sha256) == 64
