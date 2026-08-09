from __future__ import annotations

from omega_game.engines.coevolution import (
    EnvironmentGenome,
    evolve_environments,
    run_coevolution_cycle,
    seed_environments,
)
from omega_game.engines.evolution import seed_population


def test_environment_normalization_and_config_are_bounded() -> None:
    env = EnvironmentGenome(
        "extreme",
        width=100,
        height=1,
        resource_density=2.0,
        initial_energy=1000,
        harvest_energy=-3,
        move_cost=99,
        attack_cost=99,
        attack_damage=99,
        max_steps=1000,
    ).normalized()
    assert env.width == 32
    assert env.height == 4
    assert env.resource_density == 1.0
    assert env.initial_energy == 64
    assert env.harvest_energy == 0
    assert env.move_cost == 4
    assert env.attack_cost == 6
    assert env.attack_damage == 16
    assert env.max_steps == 256
    config = env.to_config()
    assert config.resource_count == config.width * config.height - 2


def test_seed_environments_is_deterministic_and_unique() -> None:
    a = seed_environments(4, seed=9)
    b = seed_environments(4, seed=9)
    assert a == b
    assert len({environment.environment_id for environment in a}) == 4


def test_coevolution_cycle_is_deterministic() -> None:
    agents = seed_population(4, seed=2)
    environments = seed_environments(3, seed=3)
    kwargs = {"train_seeds": (1, 2), "validation_seeds": (101, 102), "adversarial_limit": 2}
    a = run_coevolution_cycle(agents, environments, **kwargs)
    b = run_coevolution_cycle(agents, environments, **kwargs)
    assert a.to_json() == b.to_json()
    assert len(a.environments) == 3
    assert len(a.agents) == 4
    assert len(a.adversarial_environment_ids) == 2


def test_generalization_report_covers_every_agent() -> None:
    agents = seed_population(3, seed=15)
    environments = seed_environments(2, seed=16)
    report = run_coevolution_cycle(agents, environments, train_seeds=(5,), validation_seeds=(500,))
    assert {row.agent_id for row in report.agents} == {agent.agent_id for agent in agents}
    for row in report.agents:
        assert row.generalization_gap == round(row.train_mean_quality - row.validation_mean_quality, 6)
        assert row.validation_quality_std >= 0.0


def test_adversarial_environment_ids_follow_report_score() -> None:
    agents = seed_population(4, seed=21)
    environments = seed_environments(4, seed=22)
    report = run_coevolution_cycle(
        agents,
        environments,
        train_seeds=(7,),
        validation_seeds=(700,),
        adversarial_limit=4,
    )
    expected = [
        evaluation.environment.environment_id
        for evaluation in sorted(
            report.environments,
            key=lambda item: (item.adversarial_score, item.environment.environment_id),
            reverse=True,
        )
    ]
    assert list(report.adversarial_environment_ids) == expected


def test_environment_receipts_are_stable() -> None:
    agents = seed_population(3, seed=31)
    environments = seed_environments(2, seed=32)
    a = run_coevolution_cycle(agents, environments, train_seeds=(1,), validation_seeds=(2,))
    b = run_coevolution_cycle(agents, environments, train_seeds=(1,), validation_seeds=(2,))
    assert [row.receipt_hash for row in a.environments] == [row.receipt_hash for row in b.environments]
    assert a.receipt_hash == b.receipt_hash


def test_environment_evolution_is_deterministic_and_bounded() -> None:
    agents = seed_population(4, seed=41)
    environments = seed_environments(4, seed=42)
    report = run_coevolution_cycle(agents, environments, train_seeds=(3,), validation_seeds=(300,))
    a = evolve_environments(environments, report, generation=0, seed=43, target_size=5)
    b = evolve_environments(environments, report, generation=0, seed=43, target_size=5)
    assert a == b
    assert len(a) == 5
    assert len({environment.environment_id for environment in a}) == 5
    for environment in a:
        assert 4 <= environment.width <= 32
        assert 4 <= environment.height <= 32
        assert 0.0 <= environment.resource_density <= 1.0
        environment.to_config().validate()


def test_held_out_seed_contract_fails_closed() -> None:
    agents = seed_population(3, seed=51)
    environments = seed_environments(2, seed=52)
    try:
        run_coevolution_cycle(agents, environments, train_seeds=(1, 2), validation_seeds=(2, 3))
    except ValueError:
        pass
    else:
        raise AssertionError("overlapping train/validation seeds should fail")


def test_environment_population_contract_fails_closed() -> None:
    agents = seed_population(3, seed=61)
    env = EnvironmentGenome("same")
    try:
        run_coevolution_cycle(agents, (env, env), train_seeds=(1,), validation_seeds=(2,))
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate environment IDs should fail")
