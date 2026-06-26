from omega_auto2.capabilities import assess_capability, infer_capacity_vector
from omega_auto2.models import Workflow
from omega_auto2.workflow_synth import forge_workflow_from_task


def test_generated_workflow_gets_capacity_assessment():
    workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
    assessment = assess_capability(workflow)
    assert assessment.vector.score() > 0
    assert assessment.level.startswith("C")
    assert assessment.next_safe_exceed_steps


def test_sensitive_workflow_cannot_exceed():
    workflow = Workflow(
        id="unsafe_capacity",
        name="Unsafe capacity",
        purpose="Test capability assessment for sensitive writes",
        trigger={"type": "manual"},
        inputs=["x"],
        steps=["write_sensitive_output"],
        outputs=["result"],
        permissions={"read": ["local_context"], "write": ["public_publish"], "forbidden": []},
        oak={"required": True, "checks": ["safety"]},
    )
    assessment = assess_capability(workflow)
    assert not assessment.can_exceed()
    assert assessment.red_lock_violations


def test_capacity_vector_score_is_normalized():
    workflow = forge_workflow_from_task("résumer des papiers scientifiques")
    vector = infer_capacity_vector(workflow)
    assert 0.0 <= vector.score() <= 1.0
