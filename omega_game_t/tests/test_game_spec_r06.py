from __future__ import annotations

import json
from pathlib import Path

from omega_game.engines.game_spec import (
    ARENA_ACTIONS,
    GAME_SPEC_VERSION,
    GameSpec,
    GameSpecCompiler,
)


def _spec() -> dict:
    return {
        "spec_id": "demo",
        "version": "0.1",
        "environment": {"width": 8, "height": 7, "resource_density": 0.25, "max_steps": 16},
        "agents": [
            {"agent_id": "b", "seek_resource": 0.8, "aggression": 0.2},
            {"agent_id": "a", "seek_resource": 0.4, "aggression": 0.7},
            {"agent_id": "c", "exploration": 0.9, "conservation": 0.8},
        ],
        "rules": {"allowed_actions": ["move", "attack", "harvest", "idle"]},
        "metadata": {"purpose": "test"},
    }


def test_example_and_schema_are_valid_json() -> None:
    schema = json.loads(Path("schemas/game_spec.schema.json").read_text())
    example = json.loads(Path("examples/game_spec_arena_t0.json").read_text())
    assert schema["properties"]["version"]["const"] == GAME_SPEC_VERSION
    assert schema["additionalProperties"] is False
    assert example["version"] == GAME_SPEC_VERSION
    assert len(example["agents"]) >= 2


def test_gamespec_compile_is_deterministic_and_normalized() -> None:
    compiler = GameSpecCompiler()
    a = compiler.compile(_spec())
    b = compiler.compile(json.dumps(_spec()))
    assert a.to_json() == b.to_json()
    assert a.build_receipt == b.build_receipt
    assert [agent.agent_id for agent in a.agents] == ["a", "b", "c"]
    assert a.environment.environment_id == "demo:environment"
    assert a.config.width == 8
    assert a.accepted


def test_agent_input_order_does_not_change_receipt() -> None:
    left = _spec()
    right = _spec()
    right["agents"] = list(reversed(right["agents"]))
    compiler = GameSpecCompiler()
    assert compiler.compile(left).build_receipt == compiler.compile(right).build_receipt


def test_compiler_builds_world_and_rule_kernel() -> None:
    compiled = GameSpecCompiler().compile(_spec())
    assert set(compiled.world.entities) == {"a", "b", "c"}
    assert tuple(compiled.rule_kernel.allowed_actions) == ARENA_ACTIONS
    assert compiled.rule_kernel.required_actor_kinds == ("arena_agent",)
    assert compiled.world.world_id == "gamespec:demo:0.1"


def test_compiled_tournament_is_deterministic() -> None:
    compiled = GameSpecCompiler().compile(_spec())
    first = compiled.run_tournament(seeds=(11, 12), mirrored=True)
    second = compiled.run_tournament(seeds=(11, 12), mirrored=True)
    assert first.to_json(include_replays=False) == second.to_json(include_replays=False)


def test_agent_parameters_are_bounded_by_existing_genome_contract() -> None:
    spec = _spec()
    spec["agents"][0]["aggression"] = 99.0
    spec["agents"][1]["exploration"] = -10.0
    compiled = GameSpecCompiler().compile(spec)
    by_id = {agent.agent_id: agent for agent in compiled.agents}
    assert by_id["b"].aggression == 1.0
    assert by_id["a"].exploration == 0.0


def test_unknown_top_level_and_nested_fields_fail_closed() -> None:
    top = _spec() | {"execute_python": "print('no')"}
    try:
        GameSpec.from_dict(top)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown top-level field should fail")

    nested = _spec()
    nested["environment"]["teleport"] = True
    try:
        GameSpec.from_dict(nested)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown environment field should fail")


def test_unsupported_action_and_version_fail_closed() -> None:
    action = _spec()
    action["rules"] = {"allowed_actions": ["move", "shell_exec"]}
    try:
        GameSpec.from_dict(action)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported action should fail")

    version = _spec()
    version["version"] = "9.9"
    try:
        GameSpec.from_dict(version)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported version should fail")


def test_duplicate_agent_ids_and_small_population_fail_closed() -> None:
    duplicate = _spec()
    duplicate["agents"][1]["agent_id"] = duplicate["agents"][0]["agent_id"]
    try:
        GameSpecCompiler().compile(duplicate)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate agent IDs should fail")

    too_small = _spec()
    too_small["agents"] = too_small["agents"][:1]
    try:
        GameSpecCompiler().compile(too_small)
    except ValueError:
        pass
    else:
        raise AssertionError("population smaller than two should fail")


def test_oak_rejected_spec_cannot_run_tournament() -> None:
    spec = _spec()
    spec["metadata"] = {"purpose": "manipulative_loop"}
    compiled = GameSpecCompiler().compile(spec)
    assert not compiled.accepted
    assert "manipulative_loop" in compiled.oak_report.flags
    try:
        compiled.run_tournament(seeds=(1,))
    except ValueError:
        pass
    else:
        raise AssertionError("OAK-rejected build must not run tournament")


def test_non_object_json_root_fails_closed() -> None:
    try:
        GameSpecCompiler().compile("[]")
    except ValueError:
        pass
    else:
        raise AssertionError("JSON root must be object")
