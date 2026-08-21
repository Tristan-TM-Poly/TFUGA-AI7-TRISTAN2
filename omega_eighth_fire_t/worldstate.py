from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActorState:
    verified_capability: float = 0.0
    dependency: float = 0.0
    capture_exposure: float = 0.0
    irreversible_harm: float = 0.0


@dataclass(frozen=True)
class WorldState:
    actors: dict[str, ActorState] = field(default_factory=dict)

    def objective(self) -> float:
        return round(sum(
            actor.verified_capability
            - actor.dependency
            - actor.capture_exposure
            - actor.irreversible_harm
            for actor in self.actors.values()
        ), 9)

    def delta(self, previous: "WorldState") -> float:
        return round(self.objective() - previous.objective(), 9)
