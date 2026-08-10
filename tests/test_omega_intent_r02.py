from __future__ import annotations

from pathlib import Path

import pytest

from omega_intent_t.r02.budget import AdaptiveBudgetController
from omega_intent_t.r02.campaign import CampaignRunner, deterministic_executor, synthetic_records
from omega_intent_t.r02.completion import evaluate_completion
from omega_intent_t.r02.diff import compare_reports
from omega_intent_t.r02.ledger import IntentLedger
from omega_intent_t.r02.models import BudgetObservation, BudgetPolicy, CompletionContract, FailureRecord, WorkRecord
from omega_intent_t.r02.oak import run_oakbench
from omega_intent_t.r02.repair import RepairPlanner
from omega_intent_t.r02.stack import StackPlanner


def test_work_record_identity_is_deterministic() -> None:
    first = WorkRecord(intent_id="I", kind="code", payload={"b": 2, "a": 1})
    second = WorkRecord(intent_id="I", kind="code", payload={"a": 1, "b": 2})
    assert first.record_id == second.record_id
    assert first.content_digest == second.content_digest


def test_ledger_dedup_transitions_checkpoint_and_restart(tmp_path: Path) -> None:
    path = tmp_path / "ledger.sqlite3"
    with IntentLedger(path) as ledger:
        intent_id = ledger.ingest_intent({"id": "I", "objective": "test"})
        record = WorkRecord(intent_id=intent_id, kind="code", payload={"x": 1})
        _, created = ledger.ingest_work(record)
        _, duplicate = ledger.ingest_work(record)
        assert created is True
        assert duplicate is False
        ledger.transition(record.record_id, "ready", reason="test")
        ledger.transition(record.record_id, "running", reason="test", increment_attempt=True)
        ledger.transition(record.record_id, "validated", reason="test")
        with pytest.raises(ValueError):
            ledger.transition(record.record_id, "running", reason="illegal")
        digest = ledger.save_checkpoint(intent_id, "main", {"offset": 7})
        assert digest
        assert ledger.load_checkpoint(intent_id, "main") == {"offset": 7}
        assert ledger.summary(intent_id)["states"]["validated"] == 1
    with IntentLedger(path) as ledger:
        assert ledger.summary("I")["work_total"] == 1
        assert ledger.get_work(record.record_id).attempts == 1


def test_ledger_artifact_residual_and_lease(tmp_path: Path) -> None:
    with IntentLedger(tmp_path / "ledger.sqlite3") as ledger:
        intent_id = ledger.ingest_intent({"id": "I", "objective": "test"})
        record = WorkRecord(intent_id=intent_id, kind="code", payload={"x": 1})
        ledger.ingest_work(record)
        artifact_a = ledger.register_artifact(intent_id, "a.txt", "hello", record_id=record.record_id)
        artifact_b = ledger.register_artifact(intent_id, "a.txt", "hello", record_id=record.record_id)
        assert artifact_a == artifact_b
        residual = ledger.record_residual(intent_id, "test", {"x": 1}, record_id=record.record_id)
        assert ledger.summary(intent_id)["open_residuals"] == 1
        ledger.resolve_residual(residual)
        assert ledger.summary(intent_id)["open_residuals"] == 0
        assert ledger.acquire_lease(record.record_id, "a") is True
        assert ledger.acquire_lease(record.record_id, "b") is False
        assert ledger.release_lease(record.record_id, "a") is True


def test_ready_if_dependencies_resolved(tmp_path: Path) -> None:
    with IntentLedger(tmp_path / "ledger.sqlite3") as ledger:
        ledger.ingest_intent({"id": "I", "objective": "test"})
        parent = WorkRecord(intent_id="I", kind="parent", payload={"x": 1})
        child = WorkRecord(intent_id="I", kind="child", payload={"x": 2}, dependency_ids=(parent.record_id,))
        ledger.ingest_many((parent, child))
        assert ledger.ready_if_dependencies_resolved("I") == 1
        ledger.transition(parent.record_id, "running", reason="test")
        ledger.transition(parent.record_id, "validated", reason="test")
        assert ledger.ready_if_dependencies_resolved("I") == 1
        assert ledger.get_work(child.record_id).state == "ready"


def test_adaptive_budget_expands_and_contracts() -> None:
    controller = AdaptiveBudgetController(BudgetPolicy(initial_items=10, initial_bytes=1000))
    expanded = controller.observe(BudgetObservation(10, 10, 0, 0, 0.01))
    contracted = controller.observe(BudgetObservation(expanded.batch_items, 0, 0, expanded.batch_items, 0.01))
    assert expanded.batch_items > 10
    assert contracted.batch_items < expanded.batch_items
    assert controller.manifest()["policy"]["permanent_total_cap"] is None


def test_completion_requires_evidence_not_volume() -> None:
    incomplete = evaluate_completion(CompletionContract(requirements_total=100000, requirements_verified=99999))
    assert incomplete.complete is False
    complete = evaluate_completion(
        CompletionContract(
            requirements_total=2,
            requirements_verified=2,
            claims_total=1,
            claims_evidence_backed=1,
            build_passed=True,
            tests_passed=True,
            documentation_synced=True,
            residuals_declared=True,
        )
    )
    assert complete.complete is True


def test_repair_planner_routes_sensitive_failures_to_human_gate() -> None:
    planner = RepairPlanner()
    import_action = planner.plan(FailureRecord("WU", "ci", "ModuleNotFoundError", "ModuleNotFoundError"))
    security_action = planner.plan(FailureRecord("WU", "scan", "CVE vulnerability detected"))
    assert import_action.category == "import"
    assert import_action.automatic_candidate is True
    assert security_action.category == "security"
    assert security_action.human_gate is True


def test_stack_planner_preserves_dependencies_and_separates_risk() -> None:
    a = WorkRecord(intent_id="I", kind="a", payload={"x": 1})
    b = WorkRecord(intent_id="I", kind="b", payload={"x": 2}, dependency_ids=(a.record_id,))
    c = WorkRecord(intent_id="I", kind="c", payload={"x": 3}, dependency_ids=(b.record_id,), risk="ip_sensitive")
    shards = StackPlanner(max_items_per_shard=2).plan((a, b, c))
    assert len(shards) == 3
    assert shards[1].depends_on_shards == (shards[0].shard_id,)
    assert shards[2].requires_human_approval is True
    assert shards[2].depends_on_shards == (shards[1].shard_id,)


def test_stack_planner_blocks_missing_dependency_and_cycle() -> None:
    planner = StackPlanner()
    missing = WorkRecord(intent_id="I", kind="x", payload={}, dependency_ids=("MISSING",))
    with pytest.raises(ValueError, match="missing dependencies"):
        planner.plan((missing,))
    x = WorkRecord(intent_id="I", kind="x", payload={}, record_id="X", dependency_ids=("Y",))
    y = WorkRecord(intent_id="I", kind="y", payload={}, record_id="Y", dependency_ids=("X",))
    with pytest.raises(ValueError, match="cycle detected"):
        planner.plan((x, y))


def test_campaign_is_resumable_and_exact(tmp_path: Path) -> None:
    path = tmp_path / "ledger.sqlite3"
    with IntentLedger(path) as ledger:
        ledger.ingest_intent({"id": "I", "objective": "campaign"})
        first = CampaignRunner(
            ledger,
            controller=AdaptiveBudgetController(BudgetPolicy(initial_items=16, initial_bytes=100000)),
        ).run("I", synthetic_records("I", 100), deterministic_executor, max_records=40)
        assert first.status == "checkpointed"
        assert first.checkpoint_offset == 40
    with IntentLedger(path) as ledger:
        second = CampaignRunner(
            ledger,
            controller=AdaptiveBudgetController(BudgetPolicy(initial_items=16, initial_bytes=100000)),
        ).run("I", synthetic_records("I", 100), deterministic_executor)
        assert second.status == "completed"
        assert second.consumed == 60
        assert second.checkpoint_offset == 100
        assert ledger.summary("I")["work_total"] == 100


def test_report_diff_does_not_treat_additions_as_authority() -> None:
    report = compare_reports(
        {"validated": 10, "open_residuals": 5, "additions": 1},
        {"validated": 11, "open_residuals": 1, "additions": 1_000_000},
    )
    additions = next(item for item in report["metrics"] if item["metric"] == "additions")
    assert report["status"] == "improved"
    assert additions["contribution"] == 0
    assert report["volume_metrics_have_final_authority"] is False


def test_oakbench_passes() -> None:
    report = run_oakbench(campaign_items=256)
    assert report["passed"] is True
    assert report["permanent_total_cap"] is None
    assert report["remote_mutations"] == 0
