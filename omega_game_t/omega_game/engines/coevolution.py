from __future__ import annotations

import hashlib
import json
import random
import statistics
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .quality_diversity import quality_from_rating
from .simulation import AgentGenome, ArenaConfig
from .tournament import TournamentReport, run_round_robin


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class EnvironmentGenome:
    environment_id: str
    width: int = 12
    height: int = 12
    resource_density: float = 0.15
    initial_energy: int = 24
    harvest_energy: int = 5
    move_cost: int = 1
    attack_cost: int = 2
    attack_damage: int = 6
    max_steps: int = 96

    def normalized(self) -> "EnvironmentGenome":
        if not self.environment_id:
            raise ValueError("environment_id cannot be empty")
        return EnvironmentGenome(
            environment_id=self.environment_id,
            width=max(4, min(32, int(self.width))),
            height=max(4, min(32, int(self.height))),
            resource_density=max(0.0, min(1.0, float(self.resource_density))),
            initial_energy=max(4, min(64, int(self.initial_energy))),
            harvest_energy=max(0, min(16, int(self.harvest_energy))),
            move_cost=max(0, min(4, int(self.move_cost))),
            attack_cost=max(0, min(6, int(self.attack_cost))),
            attack_damage=max(0, min(16, int(self.attack_damage))),
            max_steps=max(8, min(256, int(self.max_steps))),
        )

    def to_config(self) -> ArenaConfig:
        env = self.normalized()
        available_cells = env.width * env.height - 2
        resource_count = min(available_cells, max(0, round(available_cells * env.resource_density)))
        config = ArenaConfig(
            width=env.width,
            height=env.height,
            max_steps=env.max_steps,
            resource_count=resource_count,
            initial_energy=env.initial_energy,
            harvest_energy=env.harvest_energy,
            move_cost=env.move_cost,
            attack_cost=env.attack_cost,
            attack_damage=env.attack_damage,
        )
        config.validate()
        return config

    def descriptor(self) -> tuple[float, ...]:
        env = self.normalized()
        return (
            (env.width - 4) / 28.0,
            (env.height - 4) / 28.0,
            env.resource_density,
            (env.initial_energy - 4) / 60.0,
            env.harvest_energy / 16.0,
            env.move_cost / 4.0,
            env.attack_cost / 6.0,
            env.attack_damage / 16.0,
            (env.max_steps - 8) / 248.0,
        )


@dataclass(frozen=True)
class EnvironmentEvaluation:
    environment: EnvironmentGenome
    train_mean_efficiency: float
    validation_mean_efficiency: float
    train_difficulty: float
    validation_difficulty: float
    difficulty_gap: float
    validation_discrimination: float
    receipt_hash: str

    @property
    def adversarial_score(self) -> float:
        return round(self.validation_difficulty + 0.10 * self.validation_discrimination, 6)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["adversarial_score"] = self.adversarial_score
        return payload


@dataclass(frozen=True)
class AgentGeneralization:
    agent_id: str
    train_mean_quality: float
    validation_mean_quality: float
    generalization_gap: float
    worst_validation_quality: float
    validation_quality_std: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoevolutionReport:
    train_seeds: tuple[int, ...]
    validation_seeds: tuple[int, ...]
    environments: tuple[EnvironmentEvaluation, ...]
    agents: tuple[AgentGeneralization, ...]
    adversarial_environment_ids: tuple[str, ...]
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_seeds": list(self.train_seeds),
            "validation_seeds": list(self.validation_seeds),
            "environments": [evaluation.to_dict() for evaluation in self.environments],
            "agents": [agent.to_dict() for agent in self.agents],
            "adversarial_environment_ids": list(self.adversarial_environment_ids),
            "receipt_hash": self.receipt_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def seed_environments(count: int, *, seed: int = 0, prefix: str = "env0") -> tuple[EnvironmentGenome, ...]:
    if count < 1:
        raise ValueError("count must be >= 1")
    rng = random.Random(int(seed))
    environments: list[EnvironmentGenome] = []
    for index in range(count):
        environments.append(
            EnvironmentGenome(
                environment_id=f"{prefix}_{index:04d}",
                width=rng.randint(6, 20),
                height=rng.randint(6, 20),
                resource_density=rng.uniform(0.03, 0.45),
                initial_energy=rng.randint(12, 40),
                harvest_energy=rng.randint(2, 10),
                move_cost=rng.randint(0, 3),
                attack_cost=rng.randint(0, 4),
                attack_damage=rng.randint(2, 12),
                max_steps=rng.randint(24, 128),
            ).normalized()
        )
    return tuple(environments)


def _tournament_metrics(tournament: TournamentReport) -> tuple[float, float, dict[str, float]]:
    efficiencies: list[float] = []
    for match in tournament.matches:
        for agent_id in (match.left.agent_id, match.right.agent_id):
            efficiencies.append(float(match.metrics[agent_id]["efficiency"]))
    mean_efficiency = statistics.fmean(efficiencies) if efficiencies else 0.0
    difficulty = 1.0 / (1.0 + max(0.0, mean_efficiency))
    qualities = {rating.agent_id: quality_from_rating(rating) for rating in tournament.ratings}
    discrimination = statistics.pstdev(qualities.values()) if len(qualities) > 1 else 0.0
    return round(mean_efficiency, 6), round(difficulty, 6), qualities | {"__discrimination__": round(discrimination, 6)}


def run_coevolution_cycle(
    population: Iterable[AgentGenome],
    environments: Iterable[EnvironmentGenome],
    *,
    train_seeds: Iterable[int] = (0, 1, 2),
    validation_seeds: Iterable[int] = (10_000, 10_001, 10_002),
    adversarial_limit: int = 3,
) -> CoevolutionReport:
    agents = tuple(agent.normalized() for agent in population)
    envs = tuple(environment.normalized() for environment in environments)
    train = tuple(int(seed) for seed in train_seeds)
    validation = tuple(int(seed) for seed in validation_seeds)
    if len(agents) < 2:
        raise ValueError("coevolution requires at least two agents")
    if len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("agent IDs must be unique")
    if not envs:
        raise ValueError("at least one environment is required")
    if len({environment.environment_id for environment in envs}) != len(envs):
        raise ValueError("environment IDs must be unique")
    if not train or not validation:
        raise ValueError("train and validation seeds cannot be empty")
    if set(train) & set(validation):
        raise ValueError("validation seeds must be held out from training seeds")
    if adversarial_limit < 1:
        raise ValueError("adversarial_limit must be >= 1")

    train_quality: dict[str, list[float]] = {agent.agent_id: [] for agent in agents}
    validation_quality: dict[str, list[float]] = {agent.agent_id: [] for agent in agents}
    evaluations: list[EnvironmentEvaluation] = []

    for environment in sorted(envs, key=lambda item: item.environment_id):
        config = environment.to_config()
        train_tournament = run_round_robin(agents, seeds=train, config=config, mirrored=True)
        validation_tournament = run_round_robin(agents, seeds=validation, config=config, mirrored=True)
        train_efficiency, train_difficulty, train_qualities = _tournament_metrics(train_tournament)
        validation_efficiency, validation_difficulty, validation_qualities = _tournament_metrics(validation_tournament)
        discrimination = float(validation_qualities.pop("__discrimination__"))
        train_qualities.pop("__discrimination__", None)
        for agent in agents:
            train_quality[agent.agent_id].append(float(train_qualities[agent.agent_id]))
            validation_quality[agent.agent_id].append(float(validation_qualities[agent.agent_id]))

        evidence = {
            "environment": asdict(environment),
            "train_seeds": list(train),
            "validation_seeds": list(validation),
            "train_mean_efficiency": train_efficiency,
            "validation_mean_efficiency": validation_efficiency,
            "train_difficulty": train_difficulty,
            "validation_difficulty": validation_difficulty,
            "validation_discrimination": discrimination,
        }
        evaluations.append(
            EnvironmentEvaluation(
                environment=environment,
                train_mean_efficiency=train_efficiency,
                validation_mean_efficiency=validation_efficiency,
                train_difficulty=train_difficulty,
                validation_difficulty=validation_difficulty,
                difficulty_gap=round(validation_difficulty - train_difficulty, 6),
                validation_discrimination=round(discrimination, 6),
                receipt_hash=_canonical_hash(evidence),
            )
        )

    agent_reports: list[AgentGeneralization] = []
    for agent in sorted(agents, key=lambda item: item.agent_id):
        train_values = train_quality[agent.agent_id]
        validation_values = validation_quality[agent.agent_id]
        train_mean = statistics.fmean(train_values)
        validation_mean = statistics.fmean(validation_values)
        agent_reports.append(
            AgentGeneralization(
                agent_id=agent.agent_id,
                train_mean_quality=round(train_mean, 6),
                validation_mean_quality=round(validation_mean, 6),
                generalization_gap=round(train_mean - validation_mean, 6),
                worst_validation_quality=round(min(validation_values), 6),
                validation_quality_std=round(statistics.pstdev(validation_values), 6) if len(validation_values) > 1 else 0.0,
            )
        )

    ranked_environments = sorted(
        evaluations,
        key=lambda item: (item.adversarial_score, item.environment.environment_id),
        reverse=True,
    )
    adversarial_ids = tuple(
        evaluation.environment.environment_id
        for evaluation in ranked_environments[: min(adversarial_limit, len(ranked_environments))]
    )
    report_payload = {
        "train_seeds": list(train),
        "validation_seeds": list(validation),
        "environments": [evaluation.to_dict() for evaluation in evaluations],
        "agents": [agent.to_dict() for agent in agent_reports],
        "adversarial_environment_ids": list(adversarial_ids),
    }
    return CoevolutionReport(
        train_seeds=train,
        validation_seeds=validation,
        environments=tuple(evaluations),
        agents=tuple(agent_reports),
        adversarial_environment_ids=adversarial_ids,
        receipt_hash=_canonical_hash(report_payload),
    )


def evolve_environments(
    environments: Iterable[EnvironmentGenome],
    report: CoevolutionReport,
    *,
    generation: int,
    seed: int = 0,
    target_size: int | None = None,
    elite_fraction: float = 0.50,
    mutation_scale: float = 0.15,
) -> tuple[EnvironmentGenome, ...]:
    envs = {environment.environment_id: environment.normalized() for environment in environments}
    if generation < 0:
        raise ValueError("generation must be >= 0")
    if not 0 < elite_fraction <= 1:
        raise ValueError("elite_fraction must be in (0, 1]")
    if mutation_scale < 0:
        raise ValueError("mutation_scale must be >= 0")
    if set(envs) != {evaluation.environment.environment_id for evaluation in report.environments}:
        raise ValueError("report environments must exactly cover environment population")
    size = len(envs) if target_size is None else int(target_size)
    if size < 1:
        raise ValueError("target_size must be >= 1")

    ranked = sorted(
        report.environments,
        key=lambda item: (item.adversarial_score, item.environment.environment_id),
        reverse=True,
    )
    elite_count = max(1, min(len(ranked), round(len(ranked) * elite_fraction)))
    elites = [envs[evaluation.environment.environment_id] for evaluation in ranked[:elite_count]]
    rng = random.Random((int(seed) * 1_000_003 + generation * 97_409 + 0xA5A5A5A5) & 0xFFFFFFFF)
    next_generation: list[EnvironmentGenome] = []

    for index, elite in enumerate(elites):
        if len(next_generation) >= size:
            break
        next_generation.append(
            EnvironmentGenome(**(asdict(elite) | {"environment_id": f"env{generation + 1}_elite_{index:04d}"})).normalized()
        )

    child_index = 0
    while len(next_generation) < size:
        parent = elites[child_index % len(elites)]
        next_generation.append(_mutate_environment(parent, rng, mutation_scale, generation + 1, child_index))
        child_index += 1
    return tuple(next_generation)


def _mutate_environment(
    parent: EnvironmentGenome,
    rng: random.Random,
    scale: float,
    generation: int,
    child_index: int,
) -> EnvironmentGenome:
    def perturb_float(value: float, span: float) -> float:
        return value + rng.gauss(0.0, scale * span)

    def perturb_int(value: int, span: int) -> int:
        return int(round(value + rng.gauss(0.0, scale * span)))

    return EnvironmentGenome(
        environment_id=f"env{generation}_child_{child_index:04d}",
        width=perturb_int(parent.width, 12),
        height=perturb_int(parent.height, 12),
        resource_density=perturb_float(parent.resource_density, 0.5),
        initial_energy=perturb_int(parent.initial_energy, 32),
        harvest_energy=perturb_int(parent.harvest_energy, 8),
        move_cost=perturb_int(parent.move_cost, 3),
        attack_cost=perturb_int(parent.attack_cost, 4),
        attack_damage=perturb_int(parent.attack_damage, 8),
        max_steps=perturb_int(parent.max_steps, 96),
    ).normalized()
