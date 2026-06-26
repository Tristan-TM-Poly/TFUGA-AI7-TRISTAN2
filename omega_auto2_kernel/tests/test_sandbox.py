from omega_auto2.sandbox import dry_run_workflow
from omega_auto2.workflow_synth import forge_workflow_from_task


def test_generated_workflow_preview_ok():
    workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
    report = dry_run_workflow(workflow)
    assert report.workflow_id == workflow.id
    assert report.ok
    assert report.planned_steps == workflow.steps
    assert report.estimated_cost_units > 0


def test_generated_workflow_preview_has_notes_field():
    workflow = forge_workflow_from_task("résumer des papiers scientifiques")
    report = dry_run_workflow(workflow)
    assert isinstance(report.notes, list)
