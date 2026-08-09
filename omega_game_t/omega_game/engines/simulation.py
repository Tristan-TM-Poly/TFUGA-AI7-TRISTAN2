from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from typing import Any

from .layout import ArenaLayout, shortest_step_candidates, walkable_neighbors


@dataclass(frozen=True)
class ArenaConfig:
    width: int = 12
    height: int = 12
    max_steps: int = 96
    resource_count: int = 20
    initial_energy: int = 24
    harvest_energy: int = 5
    move_cost: int = 1
    attack_cost: int = 2
    attack_damage: int = 6

    def validate(self) -> None:
        if self.width < 2 or self.height < 2:
            raise ValueError("arena dimensions must be >= 2")
        if self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        if self.resource_count < 0:
            raise ValueError("resource_count must be >= 0")
        if min(self.initial_energy, self.harvest_energy, self.move_cost, self.attack_cost, self.attack_damage) < 0:
            raise ValueError("energy/cost/damage values must be non-negative")


@dataclass(frozen=True)
class AgentGenome:
    agent_id: str
    seek_resource: float = 0.7
    aggression: float = 0.35
    conservation: float = 0.5
    exploration: float = 0.25

    def normalized(self) -> "AgentGenome":
        clamp = lambda x: max(0.0, min(1.0, float(x)))
        return AgentGenome(
            agent_id=self.agent_id,
            seek_resource=clamp(self.seek_resource),
            aggression=clamp(self.aggression),
            conservation=clamp(self.conservation),
            exploration=clamp(self.exploration),
        )

    def descriptor(self) -> tuple[float, float, float, float]:
        g = self.normalized()
        return (g.seek_resource, g.aggression, g.conservation, g.exploration)


@dataclass
class AgentState:
    x: int
    y: int
    energy: int
    collected: int = 0
    alive: bool = True
    attacks: int = 0
    moves: int = 0


@dataclass(frozen=True)
class MatchResult:
    seed: int
    config: ArenaConfig
    left: AgentGenome
    right: AgentGenome
    layout: ArenaLayout | None
    winner: str | None
    ticks: int
    metrics: dict[str, dict[str, float | int | bool]]
    replay: tuple[dict[str, Any], ...]
    replay_hash: str

    @property
    def layout_hash(self) -> str | None:
        return None if self.layout is None else self.layout.layout_hash

    def to_dict(self, *, include_replay: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "seed": self.seed,
            "config": asdict(self.config),
            "left": asdict(self.left),
            "right": asdict(self.right),
            "layout": None if self.layout is None else self.layout.normalized_dict(),
            "layout_hash": self.layout_hash,
            "winner": self.winner,
            "ticks": self.ticks,
            "metrics": self.metrics,
            "replay_hash": self.replay_hash,
        }
        if include_replay:
            payload["replay"] = list(self.replay)
        return payload

    def to_json(self, *, include_replay: bool = True) -> str:
        return json.dumps(self.to_dict(include_replay=include_replay), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def run_arena_t0(
    left: AgentGenome,
    right: AgentGenome,
    *,
    seed: int = 0,
    config: ArenaConfig | None = None,
    layout: ArenaLayout | None = None,
) -> MatchResult:
    """Run a small deterministic headless arena.

    Without ``layout`` Arena-T0 preserves its seeded random-resource behavior.
    With a layout, spawns/resources/obstacles are fixed, validated and included
    in replay identity. This remains a benchmark substrate, not a physical or
    biological model.
    """

    config = config or ArenaConfig()
    config.validate()
    left = left.normalized()
    right = right.normalized()
    if not left.agent_id or not right.agent_id or left.agent_id == right.agent_id:
        raise ValueError("agent IDs must be non-empty and distinct")

    rng = random.Random(int(seed))
    if layout is not None:
        layout.validate_structure()
        audit = layout.audit()
        if not audit.accepted:
            raise ValueError(f"layout failed audit: {','.join(audit.flags)}")
        if (layout.width, layout.height) != (config.width, config.height):
            raise ValueError("layout dimensions must match ArenaConfig")
        if len(layout.resources) != config.resource_count:
            raise ValueError("layout resource count must match ArenaConfig.resource_count")
        left_spawn, right_spawn = layout.left_spawn, layout.right_spawn
        resources = set(layout.resources)
        obstacles = set(layout.obstacles)
    else:
        left_spawn = (0, 0)
        right_spawn = (config.width - 1, config.height - 1)
        obstacles: set[tuple[int, int]] = set()
        blocked = {left_spawn, right_spawn}
        cells = [(x, y) for x in range(config.width) for y in range(config.height) if (x, y) not in blocked]
        resources = set(rng.sample(cells, k=min(config.resource_count, len(cells))))

    states = {
        left.agent_id: AgentState(left_spawn[0], left_spawn[1], config.initial_energy),
        right.agent_id: AgentState(right_spawn[0], right_spawn[1], config.initial_energy),
    }
    genomes = {left.agent_id: left, right.agent_id: right}
    ids = (left.agent_id, right.agent_id)
    replay: list[dict[str, Any]] = []
    ticks = 0

    for tick in range(config.max_steps):
        ticks = tick + 1
        order = ids if tick % 2 == 0 else tuple(reversed(ids))
        for actor_id in order:
            other_id = right.agent_id if actor_id == left.agent_id else left.agent_id
            actor = states[actor_id]
            other = states[other_id]
            if not actor.alive:
                continue
            action = _choose_action(actor, other, genomes[actor_id], resources, rng, config, layout)
            event = _apply_action(actor_id, other_id, action, states, resources, obstacles, config)
            event["tick"] = tick
            replay.append(event)
        for state in states.values():
            if state.energy <= 0:
                state.energy = 0
                state.alive = False
        if sum(1 for state in states.values() if state.alive) <= 1:
            break

    metrics = {agent_id: _metrics(states[agent_id], ticks) for agent_id in ids}
    left_score = float(metrics[left.agent_id]["score"])
    right_score = float(metrics[right.agent_id]["score"])
    winner = left.agent_id if left_score > right_score else right.agent_id if right_score > left_score else None

    hash_payload = {
        "seed": int(seed),
        "config": asdict(config),
        "layout": None if layout is None else layout.normalized_dict(),
        "layout_hash": None if layout is None else layout.layout_hash,
        "left": asdict(left),
        "right": asdict(right),
        "winner": winner,
        "ticks": ticks,
        "metrics": metrics,
        "replay": replay,
    }
    replay_hash = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return MatchResult(
        seed=int(seed),
        config=config,
        left=left,
        right=right,
        layout=layout,
        winner=winner,
        ticks=ticks,
        metrics=metrics,
        replay=tuple(replay),
        replay_hash=replay_hash,
    )


def _choose_action(
    actor: AgentState,
    other: AgentState,
    genome: AgentGenome,
    resources: set[tuple[int, int]],
    rng: random.Random,
    config: ArenaConfig,
    layout: ArenaLayout | None,
) -> tuple[str, tuple[int, int] | None]:
    position = (actor.x, actor.y)
    if position in resources:
        return ("harvest", None)
    distance_to_enemy = abs(actor.x - other.x) + abs(actor.y - other.y)
    if other.alive and distance_to_enemy == 1 and actor.energy > config.attack_cost and rng.random() < genome.aggression:
        return ("attack", (other.x, other.y))
    if actor.energy <= max(2, int(config.initial_energy * 0.25)) and rng.random() < genome.conservation:
        return ("stay", None)
    if resources and rng.random() < genome.seek_resource:
        target = min(resources, key=lambda p: (abs(actor.x - p[0]) + abs(actor.y - p[1]), p[0], p[1]))
        return ("move", _step_toward(position, target, rng, config, layout))
    if other.alive and rng.random() < genome.aggression:
        return ("move", _step_toward(position, (other.x, other.y), rng, config, layout))
    if rng.random() < genome.exploration:
        if layout is not None:
            choices = walkable_neighbors(layout, position)
        else:
            choices = tuple(
                candidate
                for candidate in ((actor.x + 1, actor.y), (actor.x - 1, actor.y), (actor.x, actor.y + 1), (actor.x, actor.y - 1))
                if 0 <= candidate[0] < config.width and 0 <= candidate[1] < config.height
            )
        return ("move", rng.choice(choices)) if choices else ("stay", None)
    return ("stay", None)


def _step_toward(
    position: tuple[int, int],
    target: tuple[int, int],
    rng: random.Random,
    config: ArenaConfig,
    layout: ArenaLayout | None,
) -> tuple[int, int]:
    if layout is not None:
        candidates = shortest_step_candidates(layout, position, target)
        return rng.choice(candidates) if candidates else position
    x, y = position
    tx, ty = target
    candidates: list[tuple[int, int]] = []
    if tx != x:
        candidates.append((x + (1 if tx > x else -1), y))
    if ty != y:
        candidates.append((x, y + (1 if ty > y else -1)))
    return rng.choice(candidates) if candidates else position


def _apply_action(
    actor_id: str,
    other_id: str,
    action: tuple[str, tuple[int, int] | None],
    states: dict[str, AgentState],
    resources: set[tuple[int, int]],
    obstacles: set[tuple[int, int]],
    config: ArenaConfig,
) -> dict[str, Any]:
    actor = states[actor_id]
    other = states[other_id]
    kind, target = action
    event: dict[str, Any] = {"actor": actor_id, "action": kind, "target": target, "outcome": "noop"}
    if kind == "harvest" and (actor.x, actor.y) in resources:
        resources.remove((actor.x, actor.y))
        actor.collected += 1
        actor.energy += config.harvest_energy
        event["outcome"] = "harvested"
    elif kind == "attack" and other.alive and abs(actor.x - other.x) + abs(actor.y - other.y) == 1 and actor.energy >= config.attack_cost:
        actor.energy -= config.attack_cost
        actor.attacks += 1
        other.energy = max(0, other.energy - config.attack_damage)
        if other.energy == 0:
            other.alive = False
        event["outcome"] = "hit"
        event["target"] = other_id
    elif kind == "move" and target is not None and actor.energy >= config.move_cost:
        tx, ty = target
        occupied = other.alive and (tx, ty) == (other.x, other.y)
        in_bounds = 0 <= tx < config.width and 0 <= ty < config.height
        obstacle = (tx, ty) in obstacles
        if in_bounds and not occupied and not obstacle:
            actor.x, actor.y = tx, ty
            actor.energy -= config.move_cost
            actor.moves += 1
            event["outcome"] = "moved"
        else:
            event["outcome"] = "blocked"
    elif kind == "stay":
        event["outcome"] = "stayed"
    return event


def _metrics(state: AgentState, ticks: int) -> dict[str, float | int | bool]:
    survival_bonus = 20 if state.alive else 0
    score = state.collected * 10 + state.energy + survival_bonus
    efficiency = score / max(1, ticks)
    return {
        "alive": state.alive,
        "energy": state.energy,
        "collected": state.collected,
        "attacks": state.attacks,
        "moves": state.moves,
        "score": score,
        "efficiency": round(efficiency, 6),
    }
