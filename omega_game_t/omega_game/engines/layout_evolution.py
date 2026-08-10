from __future__ import annotations

import hashlib
import json
import random
import statistics
from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable

from .evolutionary_memory import EvolutionaryMemory
from .layout import ArenaLayout
from .quality_diversity import quality_from_rating
from .simulation import AgentGenome, ArenaConfig
from .tournament import run_round_robin


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class LayoutEvolutionConfig:
    population_size: int = 8
    elite_fraction: float = 0.25
    mutation_steps: int = 2
    repair_attempts: int = 32
    fairness_threshold: float = 0.50
    train_seeds: tuple[int, ...] = (0, 1)
    validation_seeds: tuple[int, ...] = (10_000, 10_001)
    difficulty_weight: float = 1.0
    discrimination_weight: float = 0.10
    asymmetry_penalty: float = 0.10

    def validate(self) -> None:
        if self.population_size < 1:
            raise ValueError("population_size must be >= 1")
        if not 0.0 < self.elite_fraction <= 1.0:
            raise ValueError("elite_fraction must be in (0, 1]")
        if self.mutation_steps < 1:
            raise ValueError("mutation_steps must be >= 1")
        if self.repair_attempts < 1:
            raise ValueError("repair_attempts must be >= 1")
        if not 0.0 <= self.fairness_threshold <= 1.0:
            raise ValueError("fairness_threshold must be in [0, 1]")
        if not self.train_seeds or not self.validation_seeds:
            raise ValueError("train and validation seeds cannot be empty")
        if set(self.train_seeds) & set(self.validation_seeds):
            raise ValueError("train and validation seeds must be disjoint")
        if min(self.difficulty_weight, self.discrimination_weight, self.asymmetry_penalty) < 0:
            raise ValueError("score weights must be non-negative")


@dataclass(frozen=True)
class LayoutMutationResult:
    parent_hash: str
    child: ArenaLayout | None
    attempts: int
    rejected: tuple[dict[str, Any], ...]

    @property
    def accepted(self) -> bool:
        return self.child is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_hash": self.parent_hash,
            "child": None if self.child is None else self.child.normalized_dict(),
            "child_hash": None if self.child is None else self.child.layout_hash,
            "attempts": self.attempts,
            "accepted": self.accepted,
            "rejected": list(self.rejected),
        }


@dataclass(frozen=True)
class LayoutEvaluation:
    layout: ArenaLayout
    train_mean_efficiency: float
    validation_mean_efficiency: float
    train_difficulty: float
    validation_difficulty: float
    validation_discrimination: float
    resource_distance_asymmetry: float
    adversarial_score: float
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout": self.layout.normalized_dict(),
            "layout_hash": self.layout.layout_hash,
            "train_mean_efficiency": self.train_mean_efficiency,
            "validation_mean_efficiency": self.validation_mean_efficiency,
            "train_difficulty": self.train_difficulty,
            "validation_difficulty": self.validation_difficulty,
            "validation_discrimination": self.validation_discrimination,
            "resource_distance_asymmetry": self.resource_distance_asymmetry,
            "adversarial_score": self.adversarial_score,
            "receipt_hash": self.receipt_hash,
        }


@dataclass(frozen=True)
class LayoutPopulationReport:
    train_seeds: tuple[int, ...]
    validation_seeds: tuple[int, ...]
    evaluations: tuple[LayoutEvaluation, ...]
    receipt_hash: str

    def ranking(self) -> tuple[LayoutEvaluation, ...]:
        return tuple(
            sorted(
                self.evaluations,
                key=lambda row: (row.adversarial_score, row.layout.layout_hash),
                reverse=True,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_seeds": list(self.train_seeds),
            "validation_seeds": list(self.validation_seeds),
            "evaluations": [row.to_dict() for row in self.ranking()],
            "receipt_hash": self.receipt_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


@dataclass(frozen=True)
class AgentMapGeneralization:
    agent_id: str
    train_mean_quality: float
    validation_mean_quality: float
    generalization_gap: float
    worst_validation_quality: float
    validation_quality_std: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MapGeneralizationReport:
    training_layout_hashes: tuple[str, ...]
    validation_layout_hashes: tuple[str, ...]
    seeds: tuple[int, ...]
    agents: tuple[AgentMapGeneralization, ...]
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "training_layout_hashes": list(self.training_layout_hashes),
            "validation_layout_hashes": list(self.validation_layout_hashes),
            "seeds": list(self.seeds),
            "agents": [row.to_dict() for row in self.agents],
            "receipt_hash": self.receipt_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def mutate_layout(
    parent: ArenaLayout,
    *,
    seed: int,
    mutation_steps: int = 2,
    repair_attempts: int = 32,
    fairness_threshold: float = 0.50,
    memory: EvolutionaryMemory | None = None,
    generation: int | None = None,
) -> LayoutMutationResult:
    parent.validate_structure()
    if mutation_steps < 1:
        raise ValueError("mutation_steps must be >= 1")
    if repair_attempts < 1:
        raise ValueError("repair_attempts must be >= 1")
    if not 0.0 <= fairness_threshold <= 1.0:
        raise ValueError("fairness_threshold must be in [0, 1]")

    rng = random.Random(int(seed))
    rejected: list[dict[str, Any]] = []
    for attempt in range(1, repair_attempts + 1):
        candidate = parent
        operations: list[str] = []
        for _ in range(mutation_steps):
            candidate, operation = _mutate_once(candidate, rng)
            operations.append(operation)
        try:
            audit = candidate.audit(fairness_threshold=fairness_threshold)
            flags = tuple(audit.flags)
        except ValueError as exc:
            flags = (f"structural:{exc}",)

        if not flags and candidate.layout_hash != parent.layout_hash:
            return LayoutMutationResult(
                parent_hash=parent.layout_hash,
                child=candidate,
                attempts=attempt,
                rejected=tuple(rejected),
            )

        rejection = {
            "attempt": attempt,
            "candidate_hash": _candidate_hash(candidate),
            "operations": operations,
            "flags": list(flags or ("no_effect",)),
        }
        rejected.append(rejection)
        if memory is not None:
            memory.record_minus(
                "layout_mutation_rejected",
                {
                    "generation": generation,
                    "parent_hash": parent.layout_hash,
                    "seed": int(seed),
                    **rejection,
                },
            )

    return LayoutMutationResult(
        parent_hash=parent.layout_hash,
        child=None,
        attempts=repair_attempts,
        rejected=tuple(rejected),
    )


def seed_layout_population(
    base: ArenaLayout,
    count: int,
    *,
    seed: int = 0,
    mutation_steps: int = 2,
    repair_attempts: int = 64,
    fairness_threshold: float = 0.50,
    memory: EvolutionaryMemory | None = None,
) -> tuple[ArenaLayout, ...]:
    if count < 1:
        raise ValueError("count must be >= 1")
    audit = base.audit(fairness_threshold=fairness_threshold)
    if not audit.accepted:
        raise ValueError(f"base layout failed audit: {','.join(audit.flags)}")
    layouts = [base]
    seen = {base.layout_hash}
    rng = random.Random(int(seed))
    budget = max(count * repair_attempts, repair_attempts)
    for index in range(budget):
        if len(layouts) >= count:
            break
        parent = layouts[index % len(layouts)]
        result = mutate_layout(
            parent,
            seed=rng.randrange(0, 2**31),
            mutation_steps=mutation_steps,
            repair_attempts=repair_attempts,
            fairness_threshold=fairness_threshold,
            memory=memory,
            generation=0,
        )
        if result.child is not None and result.child.layout_hash not in seen:
            seen.add(result.child.layout_hash)
            layouts.append(result.child)
    if len(layouts) != count:
        raise ValueError(f"could not generate {count} unique valid layouts within bounded budget")
    return tuple(layouts)


def evaluate_layout_population(
    population: Iterable[AgentGenome],
    layouts: Iterable[ArenaLayout],
    *,
    arena_template: ArenaConfig | None = None,
    config: LayoutEvolutionConfig | None = None,
) -> LayoutPopulationReport:
    agents = tuple(agent.normalized() for agent in population)
    maps = tuple(layouts)
    cfg = config or LayoutEvolutionConfig(population_size=max(1, len(maps)))
    cfg.validate()
    if len(agents) < 2 or len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("layout evaluation requires at least two unique agents")
    if not maps:
        raise ValueError("at least one layout is required")
    if len({layout.layout_hash for layout in maps}) != len(maps):
        raise ValueError("layout population hashes must be unique")

    template = arena_template or ArenaConfig()
    rows: list[LayoutEvaluation] = []
    for layout in sorted(maps, key=lambda item: item.layout_hash):
        audit = layout.audit(fairness_threshold=cfg.fairness_threshold)
        if not audit.accepted:
            raise ValueError(f"layout {layout.layout_hash[:12]} failed audit: {','.join(audit.flags)}")
        arena = replace(
            template,
            width=layout.width,
            height=layout.height,
            resource_count=len(layout.resources),
        )
        arena.validate()
        train = run_round_robin(agents, seeds=cfg.train_seeds, config=arena, mirrored=True, layout=layout)
        validation = run_round_robin(agents, seeds=cfg.validation_seeds, config=arena, mirrored=True, layout=layout)
        train_eff, train_difficulty, _ = _tournament_metrics(train)
        validation_eff, validation_difficulty, validation_discrimination = _tournament_metrics(validation)
        score = (
            cfg.difficulty_weight * validation_difficulty
            + cfg.discrimination_weight * validation_discrimination
            - cfg.asymmetry_penalty * audit.resource_distance_asymmetry
        )
        evidence = {
            "layout_hash": layout.layout_hash,
            "train_seeds": list(cfg.train_seeds),
            "validation_seeds": list(cfg.validation_seeds),
            "train_mean_efficiency": train_eff,
            "validation_mean_efficiency": validation_eff,
            "train_difficulty": train_difficulty,
            "validation_difficulty": validation_difficulty,
            "validation_discrimination": validation_discrimination,
            "resource_distance_asymmetry": audit.resource_distance_asymmetry,
            "adversarial_score": round(score, 6),
        }
        rows.append(
            LayoutEvaluation(
                layout=layout,
                train_mean_efficiency=train_eff,
                validation_mean_efficiency=validation_eff,
                train_difficulty=train_difficulty,
                validation_difficulty=validation_difficulty,
                validation_discrimination=validation_discrimination,
                resource_distance_asymmetry=audit.resource_distance_asymmetry,
                adversarial_score=round(score, 6),
                receipt_hash=_canonical_hash(evidence),
            )
        )

    receipt = _canonical_hash(
        {
            "train_seeds": list(cfg.train_seeds),
            "validation_seeds": list(cfg.validation_seeds),
            "evaluations": [row.to_dict() for row in rows],
        }
    )
    return LayoutPopulationReport(
        train_seeds=cfg.train_seeds,
        validation_seeds=cfg.validation_seeds,
        evaluations=tuple(rows),
        receipt_hash=receipt,
    )


def evolve_layout_population(
    layouts: Iterable[ArenaLayout],
    report: LayoutPopulationReport,
    *,
    generation: int,
    seed: int,
    config: LayoutEvolutionConfig | None = None,
    memory: EvolutionaryMemory | None = None,
) -> tuple[ArenaLayout, ...]:
    maps = {layout.layout_hash: layout for layout in layouts}
    cfg = config or LayoutEvolutionConfig(population_size=len(maps))
    cfg.validate()
    if generation < 0:
        raise ValueError("generation must be >= 0")
    if set(maps) != {row.layout.layout_hash for row in report.evaluations}:
        raise ValueError("report must exactly cover layout population")

    ranked = report.ranking()
    elite_count = max(1, min(len(ranked), round(len(ranked) * cfg.elite_fraction)))
    elites = [row.layout for row in ranked[:elite_count]]
    next_maps: list[ArenaLayout] = elites[: cfg.population_size]
    seen = {layout.layout_hash for layout in next_maps}
    rng = random.Random((int(seed) * 1_000_003 + generation * 97_409 + 0x51A90A7) & 0xFFFFFFFF)
    budget = max(cfg.population_size * cfg.repair_attempts * 2, cfg.repair_attempts)

    for index in range(budget):
        if len(next_maps) >= cfg.population_size:
            break
        parent = elites[index % len(elites)]
        result = mutate_layout(
            parent,
            seed=rng.randrange(0, 2**31),
            mutation_steps=cfg.mutation_steps,
            repair_attempts=cfg.repair_attempts,
            fairness_threshold=cfg.fairness_threshold,
            memory=memory,
            generation=generation + 1,
        )
        if result.child is not None and result.child.layout_hash not in seen:
            child = result.child
            seen.add(child.layout_hash)
            next_maps.append(child)
            if memory is not None:
                memory.record_plus(
                    "layout_mutation_admitted",
                    {
                        "generation": generation + 1,
                        "parent_hash": parent.layout_hash,
                        "child_hash": child.layout_hash,
                        "attempts": result.attempts,
                    },
                )

    if len(next_maps) != cfg.population_size:
        raise ValueError("bounded layout evolution could not fill next population")
    return tuple(next_maps)


def evaluate_map_generalization(
    population: Iterable[AgentGenome],
    training_layouts: Iterable[ArenaLayout],
    validation_layouts: Iterable[ArenaLayout],
    *,
    seeds: Iterable[int] = (0, 1),
    arena_template: ArenaConfig | None = None,
    fairness_threshold: float = 0.50,
) -> MapGeneralizationReport:
    agents = tuple(agent.normalized() for agent in population)
    train_maps = tuple(training_layouts)
    validation_maps = tuple(validation_layouts)
    seed_tuple = tuple(int(seed) for seed in seeds)
    if len(agents) < 2 or len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("map generalization requires at least two unique agents")
    if not train_maps or not validation_maps:
        raise ValueError("training and validation layout sets cannot be empty")
    if not seed_tuple:
        raise ValueError("seeds cannot be empty")
    train_hashes = tuple(sorted(layout.layout_hash for layout in train_maps))
    validation_hashes = tuple(sorted(layout.layout_hash for layout in validation_maps))
    if set(train_hashes) & set(validation_hashes):
        raise ValueError("training and validation layout hashes must be disjoint")

    template = arena_template or ArenaConfig()
    train_quality: dict[str, list[float]] = {agent.agent_id: [] for agent in agents}
    validation_quality: dict[str, list[float]] = {agent.agent_id: [] for agent in agents}

    for target, layouts_group in ((train_quality, train_maps), (validation_quality, validation_maps)):
        for layout in sorted(layouts_group, key=lambda item: item.layout_hash):
            audit = layout.audit(fairness_threshold=fairness_threshold)
            if not audit.accepted:
                raise ValueError(f"layout {layout.layout_hash[:12]} failed audit: {','.join(audit.flags)}")
            arena = replace(template, width=layout.width, height=layout.height, resource_count=len(layout.resources))
            tournament = run_round_robin(agents, seeds=seed_tuple, config=arena, mirrored=True, layout=layout)
            qualities = {rating.agent_id: quality_from_rating(rating) for rating in tournament.ratings}
            for agent in agents:
                target[agent.agent_id].append(qualities[agent.agent_id])

    rows: list[AgentMapGeneralization] = []
    for agent in sorted(agents, key=lambda item: item.agent_id):
        train_values = train_quality[agent.agent_id]
        validation_values = validation_quality[agent.agent_id]
        train_mean = statistics.fmean(train_values)
        validation_mean = statistics.fmean(validation_values)
        rows.append(
            AgentMapGeneralization(
                agent_id=agent.agent_id,
                train_mean_quality=round(train_mean, 6),
                validation_mean_quality=round(validation_mean, 6),
                generalization_gap=round(train_mean - validation_mean, 6),
                worst_validation_quality=round(min(validation_values), 6),
                validation_quality_std=round(statistics.pstdev(validation_values), 6) if len(validation_values) > 1 else 0.0,
            )
        )

    payload = {
        "training_layout_hashes": list(train_hashes),
        "validation_layout_hashes": list(validation_hashes),
        "seeds": list(seed_tuple),
        "agents": [row.to_dict() for row in rows],
    }
    return MapGeneralizationReport(
        training_layout_hashes=train_hashes,
        validation_layout_hashes=validation_hashes,
        seeds=seed_tuple,
        agents=tuple(rows),
        receipt_hash=_canonical_hash(payload),
    )


def _mutate_once(layout: ArenaLayout, rng: random.Random) -> tuple[ArenaLayout, str]:
    resources = set(layout.resources)
    obstacles = set(layout.obstacles)
    protected = {layout.left_spawn, layout.right_spawn}
    all_cells = {(x, y) for x in range(layout.width) for y in range(layout.height)}
    operation = rng.choice(("move_resource", "toggle_obstacle"))

    if operation == "move_resource" and resources:
        source = rng.choice(sorted(resources))
        available = sorted(all_cells - protected - obstacles - resources)
        if not available:
            return layout, "move_resource:no_space"
        resources.remove(source)
        resources.add(rng.choice(available))
    elif operation == "toggle_obstacle":
        removable = sorted(obstacles)
        addable = sorted(all_cells - protected - obstacles - resources)
        if obstacles and (not addable or rng.random() < 0.5):
            obstacles.remove(rng.choice(removable))
        elif addable:
            obstacles.add(rng.choice(addable))
        else:
            return layout, "toggle_obstacle:no_space"
    else:
        return layout, f"{operation}:no_effect"

    return (
        ArenaLayout(
            width=layout.width,
            height=layout.height,
            left_spawn=layout.left_spawn,
            right_spawn=layout.right_spawn,
            resources=tuple(sorted(resources)),
            obstacles=tuple(sorted(obstacles)),
        ),
        operation,
    )


def _candidate_hash(layout: ArenaLayout) -> str:
    try:
        return layout.layout_hash
    except ValueError:
        return _canonical_hash(
            {
                "width": layout.width,
                "height": layout.height,
                "left_spawn": list(layout.left_spawn),
                "right_spawn": list(layout.right_spawn),
                "resources": [list(value) for value in sorted(layout.resources)],
                "obstacles": [list(value) for value in sorted(layout.obstacles)],
            }
        )


def _tournament_metrics(tournament) -> tuple[float, float, float]:
    efficiencies: list[float] = []
    for match in tournament.matches:
        for agent_id in (match.left.agent_id, match.right.agent_id):
            efficiencies.append(float(match.metrics[agent_id]["efficiency"]))
    mean_efficiency = statistics.fmean(efficiencies) if efficiencies else 0.0
    difficulty = 1.0 / (1.0 + max(0.0, mean_efficiency))
    qualities = [quality_from_rating(rating) for rating in tournament.ratings]
    discrimination = statistics.pstdev(qualities) if len(qualities) > 1 else 0.0
    return round(mean_efficiency, 6), round(difficulty, 6), round(discrimination, 6)
