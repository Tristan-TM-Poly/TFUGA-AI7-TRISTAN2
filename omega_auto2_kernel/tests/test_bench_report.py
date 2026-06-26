from omega_auto2 import TelemetrySnapshot, build_markdown_report, forge_workflow_from_task, run_bench, run_suite


def test_run_bench_returns_result():
    workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
    telemetry = TelemetrySnapshot(runs=3, successes=3, manual_steps_removed=5, artifacts_created=2, time_saved_minutes=30)
    result = run_bench(workflow, telemetry)
    assert result.workflow_id == workflow.id
    assert 0.0 <= result.capacity_score <= 1.0
    assert 0.0 <= result.proof_score <= 1.0


def test_run_suite_counts_workflows():
    workflows = [
        forge_workflow_from_task("résumer des papiers scientifiques"),
        forge_workflow_from_task("créer un dépôt GitHub OAK-safe"),
    ]
    suite = run_suite(workflows)
    assert suite["total"] == 2
    assert suite["passed"] + suite["failed"] == 2


def test_markdown_report_contains_table():
    workflow = forge_workflow_from_task("préparer un rapport AUTO2")
    report = build_markdown_report([workflow])
    assert "Bench Report" in report
    assert "| Workflow |" in report
    assert workflow.id in report
