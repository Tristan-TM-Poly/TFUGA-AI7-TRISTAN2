from omega_game.engines.code_dojo import CodeDojoEngine, demo_world as code_world
from omega_game.engines.process_alchemy import ProcessAlchemyEngine, demo_world as process_world
from omega_game.engines.prototype_world import PrototypeWorldEngine, demo_world as prototype_world
from omega_game.kernel import Action, GameEngineKernel, ResourceFlow, WorldState


def test_resource_flow_score_is_bounded():
    flow = ResourceFlow(energy=-1.0, matter=2.0, value=1.0, knowledge=1.0)

    assert 0.0 <= flow.normalized_score() <= 1.0
    assert flow.total_positive() == 4.0
    assert flow.total_negative() == 1.0


def test_world_state_requires_name_and_domain():
    try:
        WorldState(name="", domain="prototype")
    except ValueError as exc:
        assert "name" in str(exc)
    else:
        raise AssertionError("WorldState accepted empty name")


def test_action_rejects_bad_risk():
    try:
        Action(name="bad", description="bad", risk=2.0)
    except ValueError as exc:
        assert "risk" in str(exc)
    else:
        raise AssertionError("Action accepted bad risk")


def test_kernel_runs_prototype_world_best_action():
    result = GameEngineKernel().run_best_action(PrototypeWorldEngine(), prototype_world())

    assert result.engine == "PrototypeWorldEngine-T"
    assert 0.0 <= result.score <= 1.0
    assert result.oak_status in {"accepted", "caution", "blocked"}
    assert result.m_plus


def test_kernel_runs_process_alchemy_best_action():
    result = GameEngineKernel().run_best_action(ProcessAlchemyEngine(), process_world())

    assert result.engine == "ProcessAlchemyEngine-T"
    assert "no_real_world_protocol" in result.m_minus
    assert 0.0 <= result.score <= 1.0


def test_kernel_runs_code_dojo_best_action():
    result = GameEngineKernel().run_best_action(CodeDojoEngine(), code_world())

    assert result.engine == "CodeDojoEngine-T"
    assert result.after.metrics["tests"] >= result.before.metrics["tests"]
    assert result.notes


def test_simulation_result_serializes():
    result = GameEngineKernel().run_best_action(CodeDojoEngine(), code_world())
    payload = result.to_dict()

    assert set(payload) == {
        "engine",
        "before",
        "action",
        "after",
        "flow",
        "score",
        "oak_status",
        "m_plus",
        "m_minus",
        "notes",
    }
