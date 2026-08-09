from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .simulation import AgentGenome, ArenaConfig
from .tournament import RatingVector, TournamentReport, run_round_robin


@dataclass(frozen=True)
class EvolutionConfig:
    population_size: int = 12
    elite_fraction: float = 0.25
    mutation_sigma: float = 0.10
    tournament_seeds: tuple[int, ...] = (0, 1, 2)
    novelty_weight: float = 0.20
    robustness_weight: float = 0.35
    efficiency_weight: float = 0.15

    def validate(self) -> None:
        if self.population_size < 2:
            raise ValueError("population_size must be >= 2")
        if not 0 < self.elite_fraction <= 1:
            raise ValueError("elite_fraction must be in (0, 1]")
        if self.mutation_sigma < 0:
            raise ValueError("mutation_sigma must be >= 0")
        if not self.tournament_seeds:
            raise ValueError("tournament_seeds cannot be empty")


@dataclass(frozen=True)
class GenerationReport:
    generation: int
    tournament: TournamentReport
    ranked_ids: tuple[str, ...]
    elite_ids: tuple[str, ...]
    population: tuple[AgentGenome, ...]
    next_population: tuple[AgentGenome, ...]

    def to_dict(self, *, include_matches: bool = False) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "ranked_ids": list(self.ranked_ids),
            "elite_ids": list(self.elite_ids),
            "population": [asdict(agent) for agent in self.population],
            "next_population": [asdict(agent) for agent in self.next_population],
            "tournament": self.tournament.to_dict(include_replays=include_matches),
        }


@dataclass(frozen=True)
class EvolutionRun:
    seed: int
    config: EvolutionConfig
    generations: tuple[GenerationReport, ...]
    final_population: tuple[AgentGenome, ...]

    def champion(self) -> AgentGenome:
        if not self.generations:
            return self.final_population[0]
        champion_id = self.generations[-1].ranked_ids[0]
        return next(agent for agent in self.generations[-1].population if agent.agent_id == champion_id)

    def to_json(self) -> str:
        payload = {
            "seed": self.seed,
            "config": asdict(self.config),
            "generations": [generation.to_dict(include_matches=False) for generation in self.generations],
            "final_population": [asdict(agent) for agent in self.final_population],
            "champion": asdict(self.champion()),
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def seed_population(count: int, *, seed: int = 0, prefix: str = "g0") -> tuple[AgentGenome, ...]:
    if count < 2:
        raise ValueError("count must be >= 2")
    rng = random.Random(int(seed))
    return tuple(
        AgentGenome(
            agent_id=f"{prefix}_{index:04d}",
            seek_resource=rng.random(),
            aggression=rng.random(),
            conservation=rng.random(),
            exploration=rng.random(),
        )
        for index in range(count)
    )


def evolve_generation(
    population: Iterable[AgentGenome],
    *,
    generation: int,
    seed: int,
    config: EvolutionConfig | None = None,
    arena_config: ArenaConfig | None = None,
) -> GenerationReport:
    config = config or EvolutionConfig(population_size=len(tuple(population)))
    config.validate()
    agents = tuple(agent.normalized() for agent in population)
    if len(agents) < 2:
        raise ValueError("population must contain at least two agents")

    tournament = run_round_robin(agents, seeds=config.tournament_seeds, config=arena_config, mirrored=True)
    rating_by_id = {rating.agent_id: rating for rating in tournament.ratings}
    ranked = tuple(sorted(agents, key=lambda agent: (_fitness(rating_by_id[agent.agent_id], config), agent.agent_id), reverse=True))
    elite_count = max(1, min(len(ranked), round(len(ranked) * config.elite_fraction)))
    elites = ranked[:elite_count]

    rng = random.Random(_mix_seed(seed, generation))
    target_size = config.population_size
    next_population: list[AgentGenome] = []
    for index, elite in enumerate(elites):
        if len(next_population) >= target_size:
            break
        next_population.append(_renamed(elite, generation + 1, index, "elite"))

    child_index = 0
    while len(next_population) < target_size:
        parent = elites[child_index % len(elites)]
        next_population.append(_mutate(parent, rng, config.mutation_sigma, generation + 1, child_index))
        child_index += 1

    return GenerationReport(
        generation=generation,
        tournament=tournament,
        ranked_ids=tuple(agent.agent_id for agent in ranked),
        elite_ids=tuple(agent.agent_id for agent in elites),
        population=agents,
        next_population=tuple(next_population),
    )


def evolve(
    *,
    generations: int = 3,
    seed: int = 0,
    config: EvolutionConfig | None = None,
    arena_config: ArenaConfig | None = None,
    population: Iterable[AgentGenome] | None = None,
) -> EvolutionRun:
    config = config or EvolutionConfig()
    config.validate()
    if generations < 1:
        raise ValueError("generations must be >= 1")
    current = tuple(population) if population is not None else seed_population(config.population_size, seed=seed)
    if len(current) != config.population_size:
        raise ValueError("population length must equal config.population_size")

    reports: list[GenerationReport] = []
    for generation in range(generations):
        report = evolve_generation(
            current,
            generation=generation,
            seed=seed,
            config=config,
            arena_config=arena_config,
        )
        reports.append(report)
        current = report.next_population
    return EvolutionRun(seed=int(seed), config=config, generations=tuple(reports), final_population=current)


def _fitness(rating: RatingVector, config: EvolutionConfig) -> float:
    base = rating.points + 0.01 * rating.score_delta
    return (
        base
        + config.novelty_weight * rating.novelty
        + config.robustness_weight * rating.robustness
        + config.efficiency_weight * rating.efficiency
    )


def _mutate(parent: AgentGenome, rng: random.Random, sigma: float, generation: int, child_index: int) -> AgentGenome:
    def m(value: float) -> float:
        return max(0.0, min(1.0, value + rng.gauss(0.0, sigma)))

    return AgentGenome(
        agent_id=f"g{generation}_child_{child_index:04d}",
        seek_resource=m(parent.seek_resource),
        aggression=m(parent.aggression),
        conservation=m(parent.conservation),
        exploration=m(parent.exploration),
    )


def _renamed(parent: AgentGenome, generation: int, index: int, tag: str) -> AgentGenome:
    return AgentGenome(
        agent_id=f"g{generation}_{tag}_{index:04d}",
        seek_resource=parent.seek_resource,
        aggression=parent.aggression,
        conservation=parent.conservation,
        exploration=parent.exploration,
    )


def _mix_seed(seed: int, generation: int) -> int:
    return (int(seed) * 1_000_003 + int(generation) * 97_409 + 0x9E3779B9) & 0xFFFFFFFF
