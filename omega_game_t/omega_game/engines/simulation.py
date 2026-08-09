from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from typing import Any


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
    winner: str | None
    ticks: int
    metrics: dict[str, dict[str, float | int | bool]]
    replay: tuple[dict[str, Any], ...]
    replay_hash: str

    def to_dict(self, *, include_replay: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "seed": self.seed,
            "config": asdict(self.config),
            "left": asdict(self.left),
            "right": asdict(self.right),
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
) -> MatchResult:
    """Run a small deterministic headless arena.

    Arena-T0 intentionally remains simple: two agents, resources, movement,
    harvesting and adjacent combat. It is a benchmark substrate, not a claim
    that these rules model biological or social evolution.
    """

    config = config or ArenaConfig()
    config.validate()
    left = left.normalized()
    right = right.normalized()
    if not left.agent_id or not right.agent_id or left.agent_id == right.agent_id:
        raise ValueError("agent IDs must be non-empty and distinct")

    rng = random.Random(int(seed))
    states = {
        left.agent_id: AgentState(0, 0, config.initial_energy),
        right.agent_id: AgentState(config.width - 1, config.height - 1, config.initial_energy),
    }
    genomes = {left.agent_id: left, right.agent_id: right}
    ids = (left.agent_id, right.agent_id)
    blocked = {(0, 0), (config.width - 1, config.height - 1)}
    cells = [(x, y) for x in range(config.width) for y in range(config.height) if (x, y) not in blocked]
    resources = set(rng.sample(cells, k=min(config.resource_count, len(cells))))
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
            action = _choose_action(actor, other, genomes[actor_id], resources, rng, config)
            event = _apply_action(actor_id, other_id, action, states, resources, config)
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
        return ("move", _step_toward(position, target, rng))
    if other.alive and rng.random() < genome.aggression:
        return ("move", _step_toward(position, (other.x, other.y), rng))
    if rng.random() < genome.exploration:
        choices = [(actor.x + 1, actor.y), (actor.x - 1, actor.y), (actor.x, actor.y + 1), (actor.x, actor.y - 1)]
        return ("move", rng.choice(choices))
    return ("stay", None)


def _step_toward(position: tuple[int, int], target: tuple[int, int], rng: random.Random) -> tuple[int, int]:
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
        if in_bounds and not occupied:
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
