from omega_auto2.models import Workflow
from omega_auto2.oak_gate import evaluate_workflow
from omega_auto2.workflow_synth import forge_workflow_from_task


def test_generated_workflow_is_not_blocked_by_default():
    workflow = forge_workflow_from_task("créer un workflow GitHub OAK-safe")
    report = evaluate_workflow(workflow)
    assert report.status in {"dry_run_allowed", "controlled_deployment", "trusted_limited"}
    assert not report.blockers
    assert "delete_files" in report.human_approval_required_for


def test_sensitive_write_permission_blocks_workflow():
    workflow = Workflow(
        id="dangerous",
        name="Dangerous",
        purpose="Publier et supprimer sans validation",
        trigger={"type": "manual"},
        inputs=["x"],
        steps=["delete_outputs"],
        outputs=["public_result"],
        permissions={
            "read": ["local_context"],
            "write": ["delete_files", "public_publish"],
            "forbidden": [],
        },
        oak={"required": True, "checks": ["safety"]},
    )
    report = evaluate_workflow(workflow)
    assert report.status == "blocked"
    assert any("sensitive_write_permissions" in blocker for blocker in report.blockers)
