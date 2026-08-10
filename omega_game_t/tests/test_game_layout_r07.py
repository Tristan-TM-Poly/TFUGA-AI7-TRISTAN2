from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from omega_game.engines.game_spec import ARENA_ACTIONS, GameSpecCompiler
from omega_game.engines.layout import ArenaLayout, distance_map, shortest_step_candidates
from omega_game.engines.simulation import AgentGenome, ArenaConfig, run_arena_t0
from omega_game.engines.tournament import run_round_robin
from omega_game.engines.verification import audit_match, match_world_graph


def _fair_layout() -> ArenaLayout:
    return ArenaLayout(
        width=7,
        height=5,
        left_spawn=(0, 2),
        right_spawn=(6, 2),
        resources=((2, 1), (2, 3), (4, 1), (4, 3)),
        obstacles=((3, 0), (3, 4)),
    )


def _agents():
    return (
        AgentGenome("alpha", seek_resource=0.9, aggression=0.25, conservation=0.5, exploration=0.2),
        AgentGenome("beta", seek_resource=0.5, aggression=0.7, conservation=0.3, exploration=0.4),
        AgentGenome("gamma", seek_resource=0.65, aggression=0.45, conservation=0.7, exploration=0.65),
    )


def test_legacy_match_surface_omits_layout_when_absent() -> None:
    left, right, _ = _agents()
    match = run_arena_t0(left, right, seed=7, config=ArenaConfig(max_steps=8, resource_count=2))
    payload = match.to_dict(include_replay=False)
    assert match.layout is None
    assert "layout" not in payload
    assert "layout_hash" not in payload
    assert audit_match(match).accepted
    tampered = replace(match, replay_hash="0" * 64)
    assert "replay_hash_mismatch" in audit_match(tampered, check_determinism=False).flags


def test_layout_hash_is_canonical_across_resource_order() -> None:
    a = _fair_layout()
    b = ArenaLayout(
        width=7,
        height=5,
        left_spawn=(0, 2),
        right_spawn=(6, 2),
        resources=tuple(reversed(a.resources)),
        obstacles=tuple(reversed(a.obstacles)),
    )
    assert a.layout_hash == b.layout_hash
    assert a.normalized_dict() == b.normalized_dict()


def test_layout_audit_accepts_connected_symmetric_map() -> None:
    audit = _fair_layout().audit(fairness_threshold=0.1)
    assert audit.accepted
    assert audit.connected_spawns
    assert audit.resources_reachable_by_both
    assert audit.resource_distance_asymmetry == 0.0
    assert audit.spawn_distance == 6


def test_layout_audit_detects_disconnected_spawns() -> None:
    layout = ArenaLayout(
        width=5,
        height=3,
        left_spawn=(0, 1),
        right_spawn=(4, 1),
        obstacles=((2, 0), (2, 1), (2, 2)),
    )
    audit = layout.audit()
    assert not audit.accepted
    assert "spawn_disconnected" in audit.flags
    assert audit.spawn_distance is None


def test_layout_audit_detects_resource_asymmetry_policy() -> None:
    layout = ArenaLayout(width=7, height=3, left_spawn=(0, 1), right_spawn=(6, 1), resources=((1, 1),))
    strict = layout.audit(fairness_threshold=0.1)
    permissive = layout.audit(fairness_threshold=1.0)
    assert not strict.accepted
    assert "resource_distance_asymmetry" in strict.flags
    assert permissive.accepted


def test_shortest_path_avoids_obstacles() -> None:
    layout = ArenaLayout(
        width=5,
        height=3,
        left_spawn=(0, 1),
        right_spawn=(4, 1),
        obstacles=((1, 1), (2, 1), (3, 1)),
    )
    distances = distance_map(layout, layout.left_spawn)
    assert distances[layout.right_spawn] == 6
    first_steps = shortest_step_candidates(layout, layout.left_spawn, layout.right_spawn)
    assert set(first_steps) == {(0, 0), (0, 2)}


def test_structural_overlap_and_duplicate_coordinates_fail_closed() -> None:
    invalid = [
        ArenaLayout(4, 4, (0, 0), (3, 3), resources=((0, 0),)),
        ArenaLayout(4, 4, (0, 0), (3, 3), resources=((1, 1), (1, 1))),
        ArenaLayout(4, 4, (0, 0), (3, 3), resources=((1, 1),), obstacles=((1, 1),)),
    ]
    for layout in invalid:
        try:
            layout.validate_structure()
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid layout should fail: {layout}")


def test_arena_fixed_layout_is_deterministic_and_auditable() -> None:
    layout = _fair_layout()
    config = ArenaConfig(width=7, height=5, max_steps=24, resource_count=4)
    left, right, _ = _agents()
    a = run_arena_t0(left, right, seed=42, config=config, layout=layout)
    b = run_arena_t0(left, right, seed=42, config=config, layout=layout)
    assert a.replay_hash == b.replay_hash
    assert a.layout_hash == layout.layout_hash
    assert audit_match(a).accepted
    world = match_world_graph(a)
    assert any(entity.kind == "arena_layout" for entity in world.entities.values())


def test_layout_changes_replay_identity() -> None:
    config = ArenaConfig(width=7, height=5, max_steps=16, resource_count=4)
    left, right, _ = _agents()
    first = _fair_layout()
    second = ArenaLayout(
        width=7,
        height=5,
        left_spawn=(0, 2),
        right_spawn=(6, 2),
        resources=((1, 1), (1, 3), (5, 1), (5, 3)),
        obstacles=((3, 0), (3, 4)),
    )
    a = run_arena_t0(left, right, seed=9, config=config, layout=first)
    b = run_arena_t0(left, right, seed=9, config=config, layout=second)
    assert a.layout_hash != b.layout_hash
    assert a.replay_hash != b.replay_hash


def test_tournament_propagates_same_fixed_layout() -> None:
    layout = _fair_layout()
    report = run_round_robin(
        _agents(),
        seeds=(1, 2),
        config=ArenaConfig(width=7, height=5, max_steps=12, resource_count=4),
        mirrored=True,
        layout=layout,
    )
    assert report.matches
    assert {match.layout_hash for match in report.matches} == {layout.layout_hash}


def test_fixed_layout_gamespec_compiles_and_runs() -> None:
    payload = json.loads(Path("examples/game_spec_fixed_layout.json").read_text())
    compiled = GameSpecCompiler(layout_fairness_threshold=0.1).compile(payload)
    assert compiled.accepted
    assert compiled.layout is not None
    assert compiled.layout_audit is not None and compiled.layout_audit.accepted
    assert compiled.config.resource_count == len(compiled.layout.resources) == 4
    assert tuple(compiled.rule_kernel.allowed_actions) == ARENA_ACTIONS
    assert "stay" in compiled.rule_kernel.allowed_actions
    assert "idle" not in compiled.rule_kernel.allowed_actions
    tournament = compiled.run_tournament(seeds=(3,), mirrored=True)
    assert tournament.matches
    assert all(match.layout_hash == compiled.layout.layout_hash for match in tournament.matches)


def test_gamespec_without_layout_preserves_legacy_output_surface() -> None:
    payload = json.loads(Path("examples/game_spec_arena_t0.json").read_text())
    compiled = GameSpecCompiler().compile(payload)
    exported = compiled.to_dict()
    assert compiled.layout is None
    assert "layout" not in exported
    assert "layout_audit" not in exported
    assert "layout" not in compiled.spec.normalized_dict()


def test_gamespec_layout_dimension_mismatch_fails_closed() -> None:
    payload = json.loads(Path("examples/game_spec_fixed_layout.json").read_text())
    payload["environment"]["width"] = 8
    try:
        GameSpecCompiler().compile(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("environment/layout dimension mismatch should fail")


def test_unfair_layout_build_is_rejected_by_compiler_policy() -> None:
    payload = {
        "spec_id": "unfair",
        "version": "0.1",
        # Stay within EnvironmentGenome's normalized 4..32 dimensions so this
        # fixture reaches the fairness-policy gate instead of failing earlier.
        "environment": {"width": 7, "height": 4, "max_steps": 12},
        "layout": {
            "width": 7,
            "height": 4,
            "left_spawn": [0, 1],
            "right_spawn": [6, 1],
            "resources": [[1, 1]],
            "obstacles": [],
        },
        "agents": [{"agent_id": "a"}, {"agent_id": "b"}],
    }
    compiled = GameSpecCompiler(layout_fairness_threshold=0.1).compile(payload)
    assert not compiled.accepted
    assert "layout:resource_distance_asymmetry" in compiled.oak_report.flags
    try:
        compiled.run_tournament(seeds=(1,))
    except ValueError:
        pass
    else:
        raise AssertionError("layout-policy-rejected build must not run")
