from __future__ import annotations

from omega_game.engines.evolution import seed_population
from omega_game.engines.evolutionary_memory import EvolutionaryMemory
from omega_game.engines.layout import ArenaLayout
from omega_game.engines.layout_evolution import (
    LayoutEvolutionConfig,
    evaluate_layout_population,
    evaluate_map_generalization,
    evolve_layout_population,
    mutate_layout,
    seed_layout_population,
)
from omega_game.engines.simulation import ArenaConfig


def _base() -> ArenaLayout:
    return ArenaLayout(
        width=7,
        height=5,
        left_spawn=(0, 2),
        right_spawn=(6, 2),
        resources=((2, 1), (2, 3), (4, 1), (4, 3)),
        obstacles=((3, 0), (3, 4)),
    )


def _config(population_size: int) -> LayoutEvolutionConfig:
    return LayoutEvolutionConfig(
        population_size=population_size,
        elite_fraction=0.5,
        mutation_steps=1,
        repair_attempts=64,
        fairness_threshold=0.5,
        train_seeds=(1,),
        validation_seeds=(101,),
    )


def test_layout_mutation_is_deterministic_and_valid() -> None:
    parent = _base()
    a = mutate_layout(parent, seed=17, mutation_steps=2, repair_attempts=64, fairness_threshold=0.5)
    b = mutate_layout(parent, seed=17, mutation_steps=2, repair_attempts=64, fairness_threshold=0.5)
    assert a.to_dict() == b.to_dict()
    assert a.accepted
    assert a.child is not None
    assert a.child.layout_hash != parent.layout_hash
    assert a.child.audit(fairness_threshold=0.5).accepted


def test_bounded_rejections_are_exposed_and_can_feed_m_minus() -> None:
    saturated = ArenaLayout(
        width=2,
        height=2,
        left_spawn=(0, 0),
        right_spawn=(1, 1),
        resources=((0, 1), (1, 0)),
    )
    memory = EvolutionaryMemory()
    found = None
    for seed in range(32):
        result = mutate_layout(
            saturated,
            seed=seed,
            mutation_steps=1,
            repair_attempts=1,
            fairness_threshold=1.0,
            memory=memory,
            generation=2,
        )
        if not result.accepted:
            found = result
            break
    assert found is not None
    assert found.rejected
    assert memory.minus
    # MemoryRecord's canonical classifier is `category` (R0.4 contract).
    assert any(record.category == "layout_mutation_rejected" for record in memory.minus.values())


def test_seed_layout_population_is_unique_valid_and_deterministic() -> None:
    memory_a = EvolutionaryMemory()
    memory_b = EvolutionaryMemory()
    a = seed_layout_population(_base(), 4, seed=9, mutation_steps=1, repair_attempts=128, memory=memory_a)
    b = seed_layout_population(_base(), 4, seed=9, mutation_steps=1, repair_attempts=128, memory=memory_b)
    assert [layout.layout_hash for layout in a] == [layout.layout_hash for layout in b]
    assert len({layout.layout_hash for layout in a}) == 4
    assert all(layout.audit(fairness_threshold=0.5).accepted for layout in a)


def test_layout_population_evaluation_is_deterministic() -> None:
    agents = seed_population(3, seed=12)
    layouts = seed_layout_population(_base(), 3, seed=13, mutation_steps=1, repair_attempts=128)
    cfg = _config(3)
    arena = ArenaConfig(max_steps=8)
    a = evaluate_layout_population(agents, layouts, arena_template=arena, config=cfg)
    b = evaluate_layout_population(agents, layouts, arena_template=arena, config=cfg)
    assert a.to_json() == b.to_json()
    assert len(a.evaluations) == 3
    assert len({row.receipt_hash for row in a.evaluations}) == 3
    assert a.receipt_hash == b.receipt_hash


def test_layout_evolution_retains_elite_and_fills_unique_population() -> None:
    agents = seed_population(3, seed=21)
    layouts = seed_layout_population(_base(), 4, seed=22, mutation_steps=1, repair_attempts=128)
    cfg = _config(4)
    report = evaluate_layout_population(agents, layouts, arena_template=ArenaConfig(max_steps=8), config=cfg)
    memory = EvolutionaryMemory()
    a = evolve_layout_population(layouts, report, generation=0, seed=23, config=cfg, memory=memory)
    b = evolve_layout_population(layouts, report, generation=0, seed=23, config=cfg, memory=EvolutionaryMemory())
    assert [layout.layout_hash for layout in a] == [layout.layout_hash for layout in b]
    assert len(a) == 4
    assert len({layout.layout_hash for layout in a}) == 4
    elite_hash = report.ranking()[0].layout.layout_hash
    assert elite_hash in {layout.layout_hash for layout in a}
    assert all(layout.audit(fairness_threshold=cfg.fairness_threshold).accepted for layout in a)
    assert any(record.category == "layout_mutation_admitted" for record in memory.plus.values())


def test_map_generalization_uses_disjoint_layout_sets() -> None:
    agents = seed_population(3, seed=30)
    maps = seed_layout_population(_base(), 4, seed=31, mutation_steps=1, repair_attempts=128)
    report = evaluate_map_generalization(
        agents,
        maps[:2],
        maps[2:],
        seeds=(5,),
        arena_template=ArenaConfig(max_steps=8),
    )
    assert set(report.training_layout_hashes).isdisjoint(report.validation_layout_hashes)
    assert {row.agent_id for row in report.agents} == {agent.agent_id for agent in agents}
    assert report.receipt_hash
    for row in report.agents:
        # Stored means and the stored gap are independently rounded to 6 decimals,
        # so their reconstructed difference can differ by one final decimal unit.
        reconstructed_gap = round(row.train_mean_quality - row.validation_mean_quality, 6)
        assert abs(row.generalization_gap - reconstructed_gap) <= 1e-6
        assert row.worst_validation_quality >= 0.0


def test_map_generalization_is_deterministic() -> None:
    agents = seed_population(3, seed=40)
    maps = seed_layout_population(_base(), 4, seed=41, mutation_steps=1, repair_attempts=128)
    kwargs = {"seeds": (2,), "arena_template": ArenaConfig(max_steps=8)}
    a = evaluate_map_generalization(agents, maps[:2], maps[2:], **kwargs)
    b = evaluate_map_generalization(agents, maps[:2], maps[2:], **kwargs)
    assert a.to_json() == b.to_json()


def test_map_generalization_rejects_layout_leakage() -> None:
    agents = seed_population(3, seed=50)
    maps = seed_layout_population(_base(), 2, seed=51, mutation_steps=1, repair_attempts=128)
    try:
        evaluate_map_generalization(agents, maps, (maps[0],), seeds=(1,), arena_template=ArenaConfig(max_steps=8))
    except ValueError:
        pass
    else:
        raise AssertionError("train/validation layout hash leakage should fail")


def test_layout_evolution_config_rejects_seed_leakage() -> None:
    cfg = LayoutEvolutionConfig(train_seeds=(1, 2), validation_seeds=(2, 3))
    try:
        cfg.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("train/validation seed overlap should fail")
