from __future__ import annotations

import json

from omega_game import Entity, Event, OAKGate, RuleKernel, WorldGraph


def test_world_graph_adds_entities_events_and_quality_score() -> None:
    world = WorldGraph("demo_world")
    world.add_entity(Entity("player", "agent", {"role": "explorer"}))
    world.add_entity(Entity("door", "object", {"state": "closed"}))
    world.add_event(Event("e1", "player", "inspect", "door"))

    payload = world.to_dict()
    assert payload["world_id"] == "demo_world"
    assert payload["quality_score"]["mean"] > 0.0
    assert json.loads(world.to_json())["events"][0]["action"] == "inspect"


def test_rule_kernel_rejects_invalid_action_and_target() -> None:
    world = WorldGraph("rule_world")
    world.add_entity(Entity("player", "agent"))
    kernel = RuleKernel(allowed_actions=("inspect", "move"), required_actor_kinds=("agent",))

    errors = kernel.validate_event(world, Event("e2", "player", "delete", "missing"))
    assert "action_not_allowed" in errors
    assert "unknown_target" in errors


def test_oak_gate_accepts_safe_play_and_blocks_custom_risk_codes() -> None:
    gate = OAKGate(blocked_terms={"risk_code_alpha", "risk_code_beta"})
    safe = gate.evaluate_text("cooperative puzzle with consent based reward", quality_score=0.9)
    blocked = gate.evaluate_payload({"mechanic": "risk_code_alpha", "mode": "risk_code_beta"}, quality_score=0.9)

    assert safe.accepted is True
    assert blocked.accepted is False
    assert "risk_code_alpha" in blocked.flags
    assert "risk_code_beta" in blocked.flags


def test_oak_gate_warns_on_low_quality() -> None:
    gate = OAKGate()
    report = gate.evaluate_text("simple prototype", quality_score=0.4)

    assert report.accepted is False
    assert "low_game_quality_score" in report.warnings
