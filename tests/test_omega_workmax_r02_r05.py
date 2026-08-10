import pytest

from omega_workmax_t.github_telemetry import build_actions_snapshot
from omega_workmax_t.work_ir import compile_work_ir
from omega_workmax_t.evidence_subgraph import compile_evidence_subgraph
from omega_workmax_t.frontier_bridge import BackpressureState, decide_backpressure

def test_actions_snapshot_dedup_and_determinism():
    runs = [
        {"id": 10, "run_attempt": 1, "workflow_id": 1, "name": "A", "head_sha": "abc", "event": "pull_request", "status": "completed", "conclusion": "success", "created_at": "2026-08-09T20:00:00Z", "run_started_at": "2026-08-09T20:01:00Z", "updated_at": "2026-08-09T20:03:00Z"},
        {"id": 11, "run_attempt": 1, "workflow_id": 2, "name": "B", "head_sha": "abc", "event": "pull_request", "status": "queued", "conclusion": None, "created_at": "2026-08-09T20:02:00Z", "run_started_at": None, "updated_at": "2026-08-09T20:03:00Z"},
    ]
    jobs = {10: [{"id": 100, "name": "job", "status": "completed", "conclusion": "success", "created_at": "2026-08-09T20:00:00Z", "started_at": "2026-08-09T20:01:00Z", "completed_at": "2026-08-09T20:03:00Z"}]}
    a = build_actions_snapshot(runs, jobs, observed_at="2026-08-09T20:03:00Z")
    b = build_actions_snapshot(list(reversed(runs)), jobs, observed_at="2026-08-09T20:03:00Z")
    assert a == b
    assert a["run_count"] == 2
    assert a["job_count"] == 1
    assert a["queued_run_count"] == 1
    assert a["queue_seconds"]["p50"] == 60.0

def test_work_ir_compiles_all_source_types():
    report = compile_work_ir({
        "intent": {"id": "workmax-r03", "text": "Optimize repository work"},
        "changed_files": ["omega_workmax_t/cli.py", ".github/workflows/a.yml", "omega_workmax_t/models.py"],
        "issues": [{"number": 7, "title": "Fix queue routing"}],
        "capabilities": [{"capability_id": "omega-actions", "reuse_score": 1.0}],
        "oak_residues": [{"residue_id": "M-QUEUE", "description": "Queue saturation", "blocking": True}],
    })
    assert report["source_counts"] == {"changed_components": 2, "issues": 1, "capabilities": 1, "oak_residues": 1}
    ids = {p["work_id"] for p in report["packets"]}
    assert "intent:workmax-r03" in ids
    assert "capability:omega-actions" in ids
    assert "residue:m-queue" in ids
    integrate = next(p for p in report["packets"] if p["work_id"].startswith("integrate:"))
    assert len(integrate["dependencies"]) == 5
    assert report["automatic_execution_authorized"] is False

def test_evidence_subgraph_fails_closed_on_broad():
    delta = {"workflows": [
        {"workflow": "explicit.yml", "decision": "RUN_EXPLICIT_PATH_MATCH", "safe_skip": False, "matched_files": ["a.py"]},
        {"workflow": "broad.yml", "decision": "RUN_BROAD_UNROUTED", "safe_skip": False, "matched_files": ["a.py"]},
        {"workflow": "skip.yml", "decision": "SKIP_EXPLICIT_PATH_FILTER", "safe_skip": True, "matched_files": []},
    ]}
    result = compile_evidence_subgraph(delta)
    assert [x["workflow"] for x in result["selected_workflows"]] == ["broad.yml", "explicit.yml"]
    assert result["minimality_status"] == "CONSERVATIVE_NOT_MINIMAL"
    assert result["safe_skip_workflows"] == ["skip.yml"]
    assert result["automatic_skip_authorized"] is False

def test_required_workflow_overrides_skip():
    delta = {"workflows": [{"workflow": "required.yml", "decision": "SKIP_EXPLICIT_PATH_FILTER", "safe_skip": True, "matched_files": []}]}
    result = compile_evidence_subgraph(delta, required_workflows=["required.yml"])
    assert result["selected_workflows"][0]["reason"] == "REQUIRED_WORKFLOW"
    assert result["safe_skip_count"] == 0

def test_backpressure_throttles_generation_above_absorption():
    result = decide_backpressure(BackpressureState(
        generation_rate=20, validation_rate=5, queued_jobs=30,
        closure_ratio=0.25, fanout_factor=12.0, queue_waste_ratio=0.6,
    ))
    assert result["mode"] == "THROTTLE_AND_CRYSTALLIZE"
    assert result["admission_fraction"] == pytest.approx(0.25)
    assert result["no_permanent_work_count_ceiling"] is True

def test_backpressure_grows_when_healthy():
    result = decide_backpressure(BackpressureState(
        generation_rate=5, validation_rate=8, queued_jobs=0,
        closure_ratio=1.0, fanout_factor=1.0, queue_waste_ratio=0.0,
    ))
    assert result["mode"] == "GROW_AT_OBSERVED_FRONTIER"
    assert result["admission_fraction"] == 1.0
