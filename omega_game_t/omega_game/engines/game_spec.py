from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable, Mapping

from ..core import Entity, RuleKernel, WorldGraph
from ..oak import OAKGate, OAKReport
from .coevolution import EnvironmentGenome
from .layout import ArenaLayout, LayoutAudit
from .simulation import AgentGenome, ArenaConfig
from .tournament import TournamentReport, run_round_robin


GAME_SPEC_VERSION = "0.1"
ARENA_ACTIONS = ("attack", "harvest", "move", "stay")
ARENA_ACTION_ALIASES = {"idle": "stay"}


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], context: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"unknown {context} fields: {','.join(unknown)}")


@dataclass(frozen=True)
class GameAgentSpec:
    agent_id: str
    seek_resource: float = 0.5
    aggression: float = 0.5
    conservation: float = 0.5
    exploration: float = 0.5

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GameAgentSpec":
        _reject_unknown(data, {"agent_id", "seek_resource", "aggression", "conservation", "exploration"}, "agent")
        if "agent_id" not in data:
            raise ValueError("agent.agent_id is required")
        return cls(
            agent_id=str(data["agent_id"]),
            seek_resource=float(data.get("seek_resource", 0.5)),
            aggression=float(data.get("aggression", 0.5)),
            conservation=float(data.get("conservation", 0.5)),
            exploration=float(data.get("exploration", 0.5)),
        )

    def to_genome(self) -> AgentGenome:
        if not self.agent_id:
            raise ValueError("agent_id cannot be empty")
        return AgentGenome(
            agent_id=self.agent_id,
            seek_resource=self.seek_resource,
            aggression=self.aggression,
            conservation=self.conservation,
            exploration=self.exploration,
        ).normalized()


@dataclass(frozen=True)
class GameEnvironmentSpec:
    width: int = 12
    height: int = 12
    resource_density: float = 0.15
    initial_energy: int = 24
    harvest_energy: int = 5
    move_cost: int = 1
    attack_cost: int = 2
    attack_damage: int = 6
    max_steps: int = 96

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GameEnvironmentSpec":
        _reject_unknown(
            data,
            {"width", "height", "resource_density", "initial_energy", "harvest_energy", "move_cost", "attack_cost", "attack_damage", "max_steps"},
            "environment",
        )
        return cls(
            width=int(data.get("width", 12)),
            height=int(data.get("height", 12)),
            resource_density=float(data.get("resource_density", 0.15)),
            initial_energy=int(data.get("initial_energy", 24)),
            harvest_energy=int(data.get("harvest_energy", 5)),
            move_cost=int(data.get("move_cost", 1)),
            attack_cost=int(data.get("attack_cost", 2)),
            attack_damage=int(data.get("attack_damage", 6)),
            max_steps=int(data.get("max_steps", 96)),
        )

    def to_environment(self, spec_id: str) -> EnvironmentGenome:
        return EnvironmentGenome(
            environment_id=f"{spec_id}:environment",
            width=self.width,
            height=self.height,
            resource_density=self.resource_density,
            initial_energy=self.initial_energy,
            harvest_energy=self.harvest_energy,
            move_cost=self.move_cost,
            attack_cost=self.attack_cost,
            attack_damage=self.attack_damage,
            max_steps=self.max_steps,
        ).normalized()


@dataclass(frozen=True)
class GameRuleSpec:
    allowed_actions: tuple[str, ...] = ARENA_ACTIONS

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GameRuleSpec":
        _reject_unknown(data, {"allowed_actions"}, "rules")
        raw = data.get("allowed_actions", ARENA_ACTIONS)
        if not isinstance(raw, (list, tuple)):
            raise ValueError("rules.allowed_actions must be a list")
        canonical: set[str] = set()
        supported_input = set(ARENA_ACTIONS) | set(ARENA_ACTION_ALIASES)
        for value in raw:
            action = str(value)
            if action not in supported_input:
                raise ValueError(f"unsupported Arena-T0 action: {action}")
            canonical.add(ARENA_ACTION_ALIASES.get(action, action))
        if not canonical:
            raise ValueError("rules.allowed_actions cannot be empty")
        return cls(allowed_actions=tuple(sorted(canonical)))

    def to_kernel(self) -> RuleKernel:
        return RuleKernel(allowed_actions=self.allowed_actions, required_actor_kinds=("arena_agent",))


@dataclass(frozen=True)
class GameSpec:
    spec_id: str
    version: str
    environment: GameEnvironmentSpec
    agents: tuple[GameAgentSpec, ...]
    rules: GameRuleSpec = field(default_factory=GameRuleSpec)
    layout: ArenaLayout | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GameSpec":
        _reject_unknown(data, {"spec_id", "version", "environment", "agents", "rules", "layout", "metadata"}, "GameSpec")
        if "spec_id" not in data:
            raise ValueError("spec_id is required")
        spec_id = str(data["spec_id"])
        if not spec_id:
            raise ValueError("spec_id cannot be empty")
        version = str(data.get("version", GAME_SPEC_VERSION))
        if version != GAME_SPEC_VERSION:
            raise ValueError(f"unsupported GameSpec version: {version}")
        environment_raw = data.get("environment", {})
        rules_raw = data.get("rules", {})
        layout_raw = data.get("layout")
        agents_raw = data.get("agents")
        metadata = data.get("metadata", {})
        if not isinstance(environment_raw, Mapping):
            raise ValueError("environment must be an object")
        if not isinstance(rules_raw, Mapping):
            raise ValueError("rules must be an object")
        if layout_raw is not None and not isinstance(layout_raw, Mapping):
            raise ValueError("layout must be an object or null")
        if not isinstance(agents_raw, list):
            raise ValueError("agents must be a list")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        agents = tuple(GameAgentSpec.from_dict(item) for item in agents_raw if isinstance(item, Mapping))
        if len(agents) != len(agents_raw):
            raise ValueError("every agents item must be an object")
        return cls(
            spec_id=spec_id,
            version=version,
            environment=GameEnvironmentSpec.from_dict(environment_raw),
            agents=agents,
            rules=GameRuleSpec.from_dict(rules_raw),
            layout=None if layout_raw is None else ArenaLayout.from_dict(layout_raw),
            metadata=dict(metadata),
        )

    @classmethod
    def from_json(cls, text: str) -> "GameSpec":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("GameSpec JSON root must be an object")
        return cls.from_dict(payload)

    def normalized_agents(self) -> tuple[AgentGenome, ...]:
        agents = tuple(agent.to_genome() for agent in self.agents)
        if len(agents) < 2:
            raise ValueError("GameSpec requires at least two agents")
        if len({agent.agent_id for agent in agents}) != len(agents):
            raise ValueError("GameSpec agent IDs must be unique")
        return tuple(sorted(agents, key=lambda agent: agent.agent_id))

    def normalized_dict(self) -> dict[str, Any]:
        environment = self.environment.to_environment(self.spec_id)
        agents = self.normalized_agents()
        payload: dict[str, Any] = {
            "spec_id": self.spec_id,
            "version": self.version,
            "environment": asdict(environment),
            "agents": [asdict(agent) for agent in agents],
            "rules": {"allowed_actions": list(self.rules.allowed_actions)},
            "metadata": self.metadata,
        }
        if self.layout is not None:
            payload["layout"] = self.layout.normalized_dict()
        return payload


@dataclass(frozen=True)
class CompiledGame:
    spec: GameSpec
    environment: EnvironmentGenome
    config: ArenaConfig
    agents: tuple[AgentGenome, ...]
    rule_kernel: RuleKernel
    world: WorldGraph
    oak_report: OAKReport
    build_receipt: str
    layout: ArenaLayout | None = None
    layout_audit: LayoutAudit | None = None

    @property
    def accepted(self) -> bool:
        return self.oak_report.accepted and (self.layout_audit is None or self.layout_audit.accepted)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "spec": self.spec.normalized_dict(),
            "environment": asdict(self.environment),
            "config": asdict(self.config),
            "agents": [asdict(agent) for agent in self.agents],
            "rules": {"allowed_actions": list(self.rule_kernel.allowed_actions), "required_actor_kinds": list(self.rule_kernel.required_actor_kinds)},
            "world": self.world.to_dict(),
            "oak_report": self.oak_report.to_dict(),
            "accepted": self.accepted,
            "build_receipt": self.build_receipt,
        }
        if self.layout is not None:
            payload["layout"] = self.layout.normalized_dict()
            payload["layout_audit"] = None if self.layout_audit is None else self.layout_audit.to_dict()
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"

    def run_tournament(self, *, seeds: Iterable[int] = (0, 1, 2), mirrored: bool = True) -> TournamentReport:
        if not self.accepted:
            raise ValueError("compiled GameSpec is not accepted")
        return run_round_robin(self.agents, seeds=seeds, config=self.config, mirrored=mirrored, layout=self.layout)


class GameSpecCompiler:
    """Bounded compiler from declarative GameSpec to existing Omega GAME primitives."""

    def __init__(self, oak_gate: OAKGate | None = None, *, layout_fairness_threshold: float = 0.50) -> None:
        if not 0.0 <= layout_fairness_threshold <= 1.0:
            raise ValueError("layout_fairness_threshold must be in [0, 1]")
        self.oak_gate = oak_gate or OAKGate()
        self.layout_fairness_threshold = float(layout_fairness_threshold)

    def compile(self, spec: GameSpec | Mapping[str, Any] | str) -> CompiledGame:
        if isinstance(spec, str):
            parsed = GameSpec.from_json(spec)
        elif isinstance(spec, Mapping):
            parsed = GameSpec.from_dict(spec)
        elif isinstance(spec, GameSpec):
            parsed = spec
        else:
            raise TypeError("spec must be GameSpec, mapping, or JSON string")

        agents = parsed.normalized_agents()
        environment = parsed.environment.to_environment(parsed.spec_id)
        config = environment.to_config()
        layout = parsed.layout
        layout_audit: LayoutAudit | None = None
        if layout is not None:
            if (environment.width, environment.height) != (layout.width, layout.height):
                raise ValueError("GameSpec environment dimensions must match fixed layout")
            layout_audit = layout.audit(fairness_threshold=self.layout_fairness_threshold)
            config = replace(config, resource_count=len(layout.resources))
            config.validate()

        rule_kernel = parsed.rules.to_kernel()
        world = WorldGraph(world_id=f"gamespec:{parsed.spec_id}:{parsed.version}")
        for agent in agents:
            world.add_entity(Entity(entity_id=agent.agent_id, kind="arena_agent", traits=asdict(agent)))
        if layout is not None:
            world.add_entity(Entity(entity_id=f"layout:{layout.layout_hash[:16]}", kind="arena_layout", traits=layout.normalized_dict()))

        normalized_spec = parsed.normalized_dict()
        quality = world.quality_score().mean
        oak_payload = {"spec": normalized_spec, "world": world.to_dict(), "config": asdict(config)}
        oak_report = self.oak_gate.evaluate_payload(oak_payload, quality_score=quality)
        if layout_audit is not None and not layout_audit.accepted:
            layout_flags = tuple(f"layout:{flag}" for flag in layout_audit.flags)
            oak_report = OAKReport(
                accepted=False,
                flags=tuple(sorted(set(oak_report.flags + layout_flags))),
                warnings=oak_report.warnings,
                score=round(max(0.0, oak_report.score - 0.1 * len(layout_flags)), 4),
            )

        receipt_payload: dict[str, Any] = {
            "compiler": "omega_game.gamespec",
            "gamespec_version": GAME_SPEC_VERSION,
            "spec": normalized_spec,
            "config": asdict(config),
            "rules": {"allowed_actions": list(rule_kernel.allowed_actions), "required_actor_kinds": list(rule_kernel.required_actor_kinds)},
            "world_id": world.world_id,
            "oak_report": oak_report.to_dict(),
        }
        if layout is not None:
            receipt_payload["layout_hash"] = layout.layout_hash
            receipt_payload["layout_audit"] = None if layout_audit is None else layout_audit.to_dict()
        return CompiledGame(
            spec=parsed,
            environment=environment,
            config=config,
            agents=agents,
            rule_kernel=rule_kernel,
            world=world,
            oak_report=oak_report,
            build_receipt=_canonical_hash(receipt_payload),
            layout=layout,
            layout_audit=layout_audit,
        )
