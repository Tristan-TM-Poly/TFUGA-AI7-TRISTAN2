"""GameEngineOS-T kernel.

This kernel is for safe abstract simulations. It never performs external actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

from .resource_flow import ResourceFlow
from .world_state import WorldState


def default_kernel_oak_controls() -> list[str]:
    return [
        "simulation_only",
        "limits_visible",
        "no_external_action",
        "record_m_plus_and_m_minus",
    ]


@dataclass(slots=True)
class Action:
    name: str
    description: str
    expected_flow: ResourceFlow = field(default_factory=ResourceFlow)
    risk: float = 0.1
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Action.name must be non-empty.")
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("Action.risk must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["expected_flow"] = self.expected_flow.to_dict()
        return payload


@dataclass(slots=True)
class SimulationResult:
    engine: str
    before: WorldState
    action: Action
    after: WorldState
    flow: ResourceFlow
    score: float
    oak_status: str
    m_plus: list[str]
    m_minus: list[str]
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("SimulationResult.score must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "before": self.before.to_dict(),
            "action": self.action.to_dict(),
            "after": self.after.to_dict(),
            "flow": self.flow.to_dict(),
            "score": self.score,
            "oak_status": self.oak_status,
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "notes": list(self.notes),
        }


class EnginePlugin(Protocol):
    name: str

    def propose_actions(self, world: WorldState) -> list[Action]: ...

    def simulate(self, world: WorldState, action: Action) -> SimulationResult: ...


@dataclass(slots=True)
class GameEngineKernel:
    """Minimal orchestrator for engine plugins."""

    oak_controls: list[str] = field(default_factory=default_kernel_oak_controls)

    def observe(self, world: WorldState) -> dict[str, object]:
        return {
            "name": world.name,
            "domain": world.domain,
            "resources": dict(world.resources),
            "metrics": dict(world.metrics),
            "constraints": list(world.constraints),
            "oak_controls": list(self.oak_controls),
        }

    def propose_actions(self, engine: EnginePlugin, world: WorldState) -> list[Action]:
        return engine.propose_actions(world)

    def simulate(self, engine: EnginePlugin, world: WorldState, action: Action) -> SimulationResult:
        result = engine.simulate(world, action)
        if result.oak_status not in {"accepted", "caution", "blocked"}:
            raise ValueError("SimulationResult.oak_status must be accepted/caution/blocked.")
        return result

    def run_best_action(self, engine: EnginePlugin, world: WorldState) -> SimulationResult:
        actions = self.propose_actions(engine, world)
        if not actions:
            raise ValueError("Engine returned no actions.")
        best = max(actions, key=lambda action: action.expected_flow.normalized_score() - action.risk)
        return self.simulate(engine, world, best)


__all__ = ["Action", "EnginePlugin", "GameEngineKernel", "SimulationResult", "default_kernel_oak_controls"]
