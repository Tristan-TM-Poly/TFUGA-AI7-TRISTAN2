from omega_learn_t.core import ErrorRecord, MasteryAxis, SkillSpec
from omega_learn_t.scheduler import build_review_queue
from omega_learn_t.storage import JsonlStore


def test_v0_2_store_and_scheduler(tmp_path):
    store = JsonlStore(tmp_path / "state")
    spec = SkillSpec(skill="persist", goal="test persistence")
    store.save_skill(spec)
    event = store.append_event("unit", spec.skill, {"ok": True})
    assert event.skill == "persist"
    assert store.status()["events_logged"] == 1

    tasks = build_review_queue(
        skill="sched",
        mastery={MasteryAxis.RECALL: 0.2, MasteryAxis.TRANSFER: 0.5},
        invariants=["alpha", "beta"],
        errors=[ErrorRecord(name="residue", cause="unit mix", correction="fix units", future_test="retest", severity=2.5)],
    )
    assert tasks
    assert any(t.task_type == "oak_gate" for t in tasks)
