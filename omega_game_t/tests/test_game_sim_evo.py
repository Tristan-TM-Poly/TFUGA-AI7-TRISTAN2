from __future__ import annotations

from omega_game import (
    AgentGenome,
    ArenaConfig,
    EvolutionConfig,
    audit_match,
    evolve,
    fuzz_arena_t0,
    match_world_graph,
    run_arena_t0,
    run_round_robin,
    seed_population,
)


def _agents():
    return (
        AgentGenome("alpha", seek_resource=0.9, aggression=0.2, conservation=0.6, exploration=0.1),
        AgentGenome("beta", seek_resource=0.5, aggression=0.8, conservation=0.2, exploration=0.4),
    )


def test_arena_t0_is_deterministic_and_oak_auditable():
    left, right = _agents()
    config = ArenaConfig(width=8, height=8, max_steps=32, resource_count=10)
    first = run_arena_t0(left, right, seed=42, config=config)
    second = run_arena_t0(left, right, seed=42, config=config)

    assert first.replay_hash == second.replay_hash
    assert first.winner == second.winner
    audit = audit_match(first)
    assert audit.accepted
    assert audit.deterministic
    assert audit.replay_hash_valid


def test_match_projects_into_existing_world_graph_core():
    left, right = _agents()
    match = run_arena_t0(left, right, seed=5, config=ArenaConfig(max_steps=12))
    world = match_world_graph(match)

    assert set(world.entities) == {"alpha", "beta"}
    assert len(world.events) == len(match.replay)
    assert world.quality_score().mean >= 0.5


def test_round_robin_is_mirrored_and_multiseed():
    population = seed_population(3, seed=7)
    report = run_round_robin(
        population,
        seeds=(10, 11),
        config=ArenaConfig(width=6, height=6, max_steps=16, resource_count=6),
        mirrored=True,
    )

    assert len(report.matches) == 12  # C(3,2) * 2 seeds * 2 orientations
    assert len(report.ratings) == 3
    for rating in report.ratings:
        assert rating.wins + rating.draws + rating.losses == 8
        assert rating.robustness >= 0.0
        assert rating.novelty >= 0.0
        assert rating.stability > 0.0


def test_evolution_is_reproducible_and_keeps_population_budget():
    evo_config = EvolutionConfig(
        population_size=4,
        elite_fraction=0.5,
        mutation_sigma=0.05,
        tournament_seeds=(1,),
    )
    arena_config = ArenaConfig(width=5, height=5, max_steps=12, resource_count=4)
    first = evolve(generations=2, seed=123, config=evo_config, arena_config=arena_config)
    second = evolve(generations=2, seed=123, config=evo_config, arena_config=arena_config)

    assert first.to_json() == second.to_json()
    assert len(first.final_population) == 4
    assert len(first.generations) == 2
    assert first.champion().agent_id == second.champion().agent_id


def test_fuzzer_preserves_core_invariants():
    report = fuzz_arena_t0(cases=12, seed=99)
    assert report.accepted, report.to_json()
    assert report.accepted_cases == 12
