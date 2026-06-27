"""World state primitive for GameEngineOS-T."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class WorldState:
    """Serializable state shared by simulation engines."""

    name: str
    domain: str
    resources: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    memory: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("WorldState.name must be non-empty.")
        if not self.domain.strip():
            raise ValueError("WorldState.domain must be non-empty.")
        for collection_name, collection in (("resources", self.resources), ("metrics", self.metrics)):
            for key, value in collection.items():
                if not isinstance(key, str) or not key:
                    raise ValueError(f"{collection_name} keys must be non-empty strings.")
                if not isinstance(value, (int, float)):
                    raise TypeError(f"{collection_name}.{key} must be numeric.")

    def get(self, key: str, default: float = 0.0) -> float:
        return float(self.resources.get(key, self.metrics.get(key, default)))

    def with_metric(self, key: str, value: float) -> "WorldState":
        metrics = dict(self.metrics)
        metrics[key] = float(value)
        return WorldState(
            name=self.name,
            domain=self.domain,
            resources=dict(self.resources),
            metrics=metrics,
            memory=list(self.memory),
            constraints=list(self.constraints),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


__all__ = ["WorldState"]
