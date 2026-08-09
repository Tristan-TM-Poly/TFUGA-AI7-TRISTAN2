from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from typing import Any

from ..core import Entity, Event, WorldGraph
from ..oak import OAKGate, OAKReport
from .simulation import AgentGenome, ArenaConfig, MatchResult, run_arena_t0


@dataclass(frozen=True)
class SimulationAudit:
    accepted: bool
    flags: tuple[str, ...]
    warnings: tuple[str, ...]
    deterministic: bool
    replay_hash_valid: bool
    oak_report: OAKReport
    world_quality: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "flags": list(self.flags),
            "warnings": list(self.warnings),
            "deterministic": self.deterministic,
            "replay_hash_valid": self.replay_hash_valid,
            "oak_report": self.oak_report.to_dict(),
            "world_quality": self.world_quality,
        }


@dataclass(frozen=True)
class FuzzFailure:
    case_index: int
    seed: int
    flags: tuple[str, ...]


@dataclass(frozen=True)
class FuzzReport:
    cases: int
    seed: int
    accepted_cases: int
    failures: tuple[FuzzFailure, ...]

    @property
    def accepted(self) -> bool:
        return not self.failures and self.accepted_cases == self.cases

    def to_json(self) -> str:
        payload = {
            "cases": self.cases,
            "seed": self.seed,
            "accepted_cases": self.accepted_cases,
            "accepted": self.accepted,
            "failures": [asdict(failure) for failure in self.failures],
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def match_world_graph(match: MatchResult) -> WorldGraph:
    """Project an Arena-T0 replay and optional fixed layout into WorldGraph."""

    world = WorldGraph(world_id=f"arena-t0:{match.seed}:{match.replay_hash[:12]}")
    for genome in (match.left, match.right):
        world.add_entity(Entity(entity_id=genome.agent_id, kind="arena_agent", traits=asdict(genome)))
    if match.layout is not None:
        world.add_entity(
            Entity(
                entity_id=f"layout:{match.layout.layout_hash[:16]}",
                kind="arena_layout",
                traits=match.layout.normalized_dict(),
            )
        )
    for index, replay_event in enumerate(match.replay):
        target = replay_event.get("target")
        target_id = target if isinstance(target, str) and target in world.entities else None
        payload = {key: value for key, value in replay_event.items() if key not in {"actor", "action", "target"}}
        world.add_event(
            Event(
                event_id=f"event-{index:06d}",
                actor_id=str(replay_event["actor"]),
                action=str(replay_event["action"]),
                target_id=target_id,
                payload=payload,
            )
        )
    return world


def audit_match(
    match: MatchResult,
    *,
    check_determinism: bool = True,
    layout_fairness_threshold: float = 0.50,
) -> SimulationAudit:
    if not 0.0 <= layout_fairness_threshold <= 1.0:
        raise ValueError("layout_fairness_threshold must be in [0, 1]")
    flags: list[str] = []
    warnings: list[str] = []
    config = match.config
    try:
        config.validate()
    except ValueError as exc:
        flags.append(f"invalid_config:{exc}")

    if match.layout is not None:
        try:
            layout_audit = match.layout.audit(fairness_threshold=layout_fairness_threshold)
            if not layout_audit.accepted:
                flags.extend(f"layout:{flag}" for flag in layout_audit.flags)
            if (match.layout.width, match.layout.height) != (config.width, config.height):
                flags.append("layout:dimension_mismatch")
            if len(match.layout.resources) != config.resource_count:
                flags.append("layout:resource_count_mismatch")
        except ValueError as exc:
            flags.append(f"invalid_layout:{exc}")

    ids = (match.left.agent_id, match.right.agent_id)
    if match.ticks < 1 or match.ticks > config.max_steps:
        flags.append("tick_count_out_of_bounds")
    if match.winner is not None and match.winner not in ids:
        flags.append("unknown_winner")
    for agent_id in ids:
        metrics = match.metrics.get(agent_id)
        if metrics is None:
            flags.append(f"missing_metrics:{agent_id}")
            continue
        if float(metrics.get("energy", -1)) < 0:
            flags.append(f"negative_energy:{agent_id}")
        if float(metrics.get("score", -1)) < 0:
            flags.append(f"negative_score:{agent_id}")

    replay_hash_valid = _replay_digest(match) == match.replay_hash
    if not replay_hash_valid:
        flags.append("replay_hash_mismatch")

    deterministic = True
    if check_determinism:
        repeated = run_arena_t0(match.left, match.right, seed=match.seed, config=match.config, layout=match.layout)
        deterministic = repeated.replay_hash == match.replay_hash and repeated.winner == match.winner
        if not deterministic:
            flags.append("determinism_failure")

    world = match_world_graph(match)
    quality = world.quality_score().mean
    oak_report = OAKGate().evaluate_payload(world.to_dict(), quality_score=quality)
    if not oak_report.accepted:
        flags.extend(f"oak:{flag}" for flag in oak_report.flags)
    warnings.extend(oak_report.warnings)
    accepted = not flags and oak_report.accepted and replay_hash_valid and deterministic
    return SimulationAudit(
        accepted=accepted,
        flags=tuple(sorted(set(flags))),
        warnings=tuple(sorted(set(warnings))),
        deterministic=deterministic,
        replay_hash_valid=replay_hash_valid,
        oak_report=oak_report,
        world_quality=quality,
    )


def fuzz_arena_t0(*, cases: int = 100, seed: int = 0) -> FuzzReport:
    if cases < 1:
        raise ValueError("cases must be >= 1")
    rng = random.Random(int(seed))
    failures: list[FuzzFailure] = []
    accepted_cases = 0
    for case_index in range(cases):
        width = rng.randint(2, 10)
        height = rng.randint(2, 10)
        config = ArenaConfig(
            width=width,
            height=height,
            max_steps=rng.randint(1, 64),
            resource_count=rng.randint(0, max(0, width * height - 2)),
            initial_energy=rng.randint(1, 40),
            harvest_energy=rng.randint(0, 12),
            move_cost=rng.randint(0, 3),
            attack_cost=rng.randint(0, 4),
            attack_damage=rng.randint(0, 10),
        )
        left = _random_genome(rng, f"f{case_index}-a")
        right = _random_genome(rng, f"f{case_index}-b")
        case_seed = rng.randrange(0, 2**31)
        match = run_arena_t0(left, right, seed=case_seed, config=config)
        audit = audit_match(match, check_determinism=True)
        if audit.accepted:
            accepted_cases += 1
        else:
            failures.append(FuzzFailure(case_index=case_index, seed=case_seed, flags=audit.flags))
    return FuzzReport(cases=cases, seed=int(seed), accepted_cases=accepted_cases, failures=tuple(failures))


def _random_genome(rng: random.Random, agent_id: str) -> AgentGenome:
    return AgentGenome(
        agent_id=agent_id,
        seek_resource=rng.uniform(-0.25, 1.25),
        aggression=rng.uniform(-0.25, 1.25),
        conservation=rng.uniform(-0.25, 1.25),
        exploration=rng.uniform(-0.25, 1.25),
    )


def _replay_digest(match: MatchResult) -> str:
    payload = {
        "seed": match.seed,
        "config": asdict(match.config),
        "layout": None if match.layout is None else match.layout.normalized_dict(),
        "layout_hash": match.layout_hash,
        "left": asdict(match.left),
        "right": asdict(match.right),
        "winner": match.winner,
        "ticks": match.ticks,
        "metrics": match.metrics,
        "replay": list(match.replay),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
