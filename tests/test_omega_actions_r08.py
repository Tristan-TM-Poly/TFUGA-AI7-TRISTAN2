from __future__ import annotations

from omega_actions_t.auto_optimizer import compile_candidate, propose_actions
from omega_actions_t.promotion import compare_telemetry


def _telemetry(duration: float, failure: float, completed: int = 20) -> dict:
    return {
        "aggregate": {
            "completed_runs": completed,
            "failure_rate_completed": failure,
            "duration_seconds": {"p95": duration},
            "queue_seconds": {"p95": 20.0},
        }
    }


def test_candidate_plan_never_auto_applies_broad_routing() -> None:
    evidence = {
        "evidence_state": "STATIC_PLUS_DELTA",
        "top_candidates": [{"workflow": ".github/workflows/ci.yml", "priority_score": 9.0}],
        "static": {
            "workflows": [{
                "path": ".github/workflows/ci.yml",
                "recommendations": [{"id": "cancel-obsolete-runs"}, {"id": "bound-job-runtime"}],
            }]
        },
        "delta": {
            "workflows": [{
                "workflow": ".github/workflows/ci.yml",
                "decision": "RUN_BROAD_UNROUTED",
            }]
        },
    }
    report = propose_actions(evidence)
    kinds = {item["kind"] for item in report["proposals"][0]["actions"]}
    assert "ADD_CONCURRENCY_CANDIDATE" in kinds
    assert "RESEARCH_DELTA_ROUTING" in kinds
    assert report["automatic_repository_mutation"] is False
    assert all(action["automatic_apply"] is False for action in report["proposals"][0]["actions"])


def test_ir_candidate_adds_pull_request_concurrency_without_mutating_baseline() -> None:
    baseline = {
        "name": "CI",
        "on": {"pull_request": {"paths": ["src/**"]}},
        "permissions": {"contents": "read"},
        "jobs": [{"id": "test", "timeout_minutes": 5, "steps": [{"kind": "run", "run": "pytest -q"}]}],
    }
    result = compile_candidate(
        baseline,
        workflow_path=".github/workflows/generated.yml",
        add_pr_concurrency=True,
    )
    assert "concurrency:" in result["candidate_yaml"]
    assert "cancel-in-progress: true" in result["candidate_yaml"]
    assert "concurrency" not in baseline
    assert result["automatic_repository_mutation"] is False


def test_promotion_gate_promotes_only_with_proof_and_material_gain() -> None:
    proof = {
        "coverage_preserved": True,
        "required_checks_preserved": True,
        "permissions_non_escalating": True,
        "rollback_ready": True,
    }
    good = compare_telemetry(_telemetry(100, 0.05), _telemetry(80, 0.05), proof_gates=proof)
    assert good["decision"] == "PROMOTE_CANDIDATE"
    regression = compare_telemetry(_telemetry(100, 0.05), _telemetry(70, 0.10), proof_gates=proof)
    assert regression["decision"] == "REJECT_REGRESSION"
    unknown = dict(proof)
    unknown["coverage_preserved"] = None
    held = compare_telemetry(_telemetry(100, 0.05), _telemetry(70, 0.05), proof_gates=unknown)
    assert held["decision"] == "INSUFFICIENT_EVIDENCE"
