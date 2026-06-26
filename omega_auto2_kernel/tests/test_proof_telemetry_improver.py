from omega_auto2 import TelemetrySnapshot, improve_draft, prove_workflow
from omega_auto2.workflow_synth import forge_workflow_from_task


def test_telemetry_value_score_is_normalized():
    telemetry = TelemetrySnapshot(
        runs=10,
        successes=8,
        failures=2,
        manual_steps_removed=12,
        errors_prevented=4,
        artifacts_created=5,
        time_saved_minutes=120,
        cost_units=4,
        noise_events=1,
    )
    assert 0.0 <= telemetry.value_score() <= 1.0
    assert telemetry.success_rate == 0.8


def test_proof_of_workflow_returns_payload():
    workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
    telemetry = TelemetrySnapshot(runs=5, successes=5, manual_steps_removed=10, artifacts_created=4, time_saved_minutes=90)
    proof = prove_workflow(workflow, telemetry)
    data = proof.to_dict()
    assert data["workflow_id"] == workflow.id
    assert 0.0 <= data["value_score"] <= 1.0


def test_improve_draft_adds_or_preserves_steps():
    workflow = forge_workflow_from_task("résumer des papiers scientifiques")
    improved = improve_draft(workflow)
    assert improved.status == "draft"
    assert len(improved.steps) >= len(workflow.steps)
