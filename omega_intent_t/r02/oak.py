from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any

from .budget import AdaptiveBudgetController
from .campaign import CampaignRunner, deterministic_executor, synthetic_records
from .completion import evaluate_completion
from .diff import compare_reports
from .ledger import IntentLedger
from .models import BudgetObservation, BudgetPolicy, CompletionContract, FailureRecord, WorkRecord
from .repair import RepairPlanner
from .stack import StackPlanner


def run_oakbench(*, campaign_items: int = 4096) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append({"check_id": check_id, "passed": bool(passed), "evidence": evidence})

    with tempfile.TemporaryDirectory(prefix="omega-intent-r02-oak-") as directory:
        root = Path(directory)
        ledger_path = root / "ledger.sqlite3"
        with IntentLedger(ledger_path) as ledger:
            intent_id = ledger.ingest_intent({"id": "INTENT-OAK-R02", "objective": "validate R0.2 invariants"})
            first = WorkRecord(intent_id=intent_id, kind="foundation", payload={"value": 1})
            stored, created = ledger.ingest_work(first)
            duplicate, created_again = ledger.ingest_work(first)
            check("ledger_deduplicates_content", created and not created_again and stored.record_id == duplicate.record_id, stored.record_id)

            ledger.transition(first.record_id, "ready", reason="oak")
            ledger.transition(first.record_id, "running", reason="oak", increment_attempt=True)
            ledger.transition(first.record_id, "validated", reason="oak")
            illegal_blocked = False
            try:
                ledger.transition(first.record_id, "running", reason="illegal")
            except ValueError:
                illegal_blocked = True
            check("illegal_state_transition_blocked", illegal_blocked, ledger.get_work(first.record_id).to_dict())

            digest = ledger.save_checkpoint(intent_id, "oak", {"offset": 17, "state": "verified"})
            checkpoint = ledger.load_checkpoint(intent_id, "oak")
            check("checkpoint_roundtrip", checkpoint == {"offset": 17, "state": "verified"}, digest)

            artifact_a = ledger.register_artifact(intent_id, "reports/oak.json", "{}")
            artifact_b = ledger.register_artifact(intent_id, "reports/oak.json", "{}")
            check("artifact_content_identity", artifact_a == artifact_b, artifact_a)

            acquired = ledger.acquire_lease(first.record_id, "worker-a", ttl_seconds=60)
            rejected = not ledger.acquire_lease(first.record_id, "worker-b", ttl_seconds=60)
            released = ledger.release_lease(first.record_id, "worker-a")
            check("cooperative_lease", acquired and rejected and released, {"acquired": acquired, "rejected": rejected, "released": released})

            campaign_intent = ledger.ingest_intent({"id": "INTENT-OAK-CAMPAIGN", "objective": "campaign"})
            controller = AdaptiveBudgetController(BudgetPolicy(initial_items=64, initial_bytes=128_000))
            report = CampaignRunner(ledger, controller=controller).run(
                campaign_intent,
                synthetic_records(campaign_intent, campaign_items),
                deterministic_executor,
            )
            check(
                "campaign_exact_consumption",
                report.consumed == campaign_items and report.source_exhausted and report.failed == 0,
                report.to_dict(),
            )
            summary = ledger.summary(campaign_intent)
            check("ledger_campaign_summary", summary["work_total"] == campaign_items, summary)

        with IntentLedger(ledger_path) as reopened:
            persisted = reopened.summary("INTENT-OAK-CAMPAIGN")
            check("sqlite_restart_persistence", persisted["work_total"] == campaign_items, persisted)

    grow = AdaptiveBudgetController(BudgetPolicy(initial_items=10, initial_bytes=10_000))
    grown = grow.observe(BudgetObservation(processed=10, accepted=10, rejected=0, failed=0, elapsed_seconds=0.1))
    shrunk = grow.observe(BudgetObservation(processed=grown.batch_items, accepted=0, rejected=0, failed=grown.batch_items, elapsed_seconds=0.1))
    check("adaptive_budget_grows_and_shrinks", grown.batch_items > 10 and shrunk.batch_items < grown.batch_items, {"grown": grown.to_dict(), "shrunk": shrunk.to_dict()})

    complete = evaluate_completion(
        CompletionContract(
            requirements_total=10,
            requirements_verified=10,
            claims_total=5,
            claims_evidence_backed=5,
            build_passed=True,
            tests_passed=True,
            documentation_synced=True,
            benchmarks_completed=2,
            residuals_declared=True,
        )
    )
    incomplete = evaluate_completion(CompletionContract(requirements_total=10, requirements_verified=3))
    check("completion_contract_not_volume_claim", complete.complete and not incomplete.complete, {"complete": complete.to_dict(), "incomplete": incomplete.to_dict()})

    planner = StackPlanner(max_items_per_shard=2, max_bytes_per_shard=10_000)
    a = WorkRecord(intent_id="I", kind="a", payload={"a": 1})
    b = WorkRecord(intent_id="I", kind="b", payload={"b": 2}, dependency_ids=(a.record_id,))
    c = WorkRecord(intent_id="I", kind="c", payload={"c": 3}, dependency_ids=(b.record_id,), risk="ip_sensitive")
    stack = planner.plan((a, b, c))
    check("stack_preserves_dependencies_and_gates_risk", len(stack) == 3 and stack[-1].requires_human_approval and stack[-1].depends_on_shards, [item.to_dict() for item in stack])

    cycle_blocked = False
    x = WorkRecord(intent_id="I", kind="x", payload={"x": 1}, record_id="X", dependency_ids=("Y",))
    y = WorkRecord(intent_id="I", kind="y", payload={"y": 1}, record_id="Y", dependency_ids=("X",))
    try:
        planner.plan((x, y))
    except ValueError:
        cycle_blocked = True
    check("stack_cycle_blocked", cycle_blocked, [x.to_dict(), y.to_dict()])

    failure = FailureRecord("WU", "ci", "ModuleNotFoundError: omega_missing", "ModuleNotFoundError")
    repair = RepairPlanner().plan(failure)
    check("repair_classification", repair.category == "import" and repair.automatic_candidate, repair.to_dict())

    diff = compare_reports(
        {"validated": 10, "open_residuals": 4, "additions": 1000},
        {"validated": 12, "open_residuals": 1, "additions": 100000},
    )
    check("diff_ignores_volume_as_authority", diff["status"] == "improved" and diff["volume_metrics_have_final_authority"] is False, diff)

    passed = all(item["passed"] for item in checks)
    return {
        "schema": "omega-intent-r02-oakbench/v2",
        "passed": passed,
        "checks": checks,
        "campaign_items": campaign_items,
        "theorem_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
        "arbitrary_intent_completion_claimed": False,
        "permanent_total_cap": None,
        "remote_mutations": 0,
        "automatic_merge": False,
    }
