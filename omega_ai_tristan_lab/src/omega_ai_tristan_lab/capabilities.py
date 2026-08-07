"""Capability manifests and the executable Tristan capability graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True, slots=True)
class CapabilitySpec:
    id: str
    task: str
    description: str = ""
    input_kind: str = "mapping"
    output_kind: str = "mapping"
    input_schema: str = "tristan.any"
    output_schema: str = "tristan.any"
    permissions: tuple[str, ...] = ("PURE",)
    deterministic: bool = True
    cost_weight: float = 1.0
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CapabilityProvider:
    capability: CapabilitySpec
    plugin: str
    source: str
    distribution: str = ""
    version: str = ""
    repository: str = ""
    commit: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capability"] = self.capability.to_dict()
        return data


class CapabilityGraph:
    """Capability↔provider graph with deterministic resolution."""

    def __init__(self) -> None:
        self._providers: dict[str, list[CapabilityProvider]] = {}

    def add(
        self,
        *,
        plugin: str,
        source: str,
        specs: Iterable[CapabilitySpec],
        distribution: str = "",
        version: str = "",
        repository: str = "",
        commit: str = "",
    ) -> None:
        for spec in specs:
            provider = CapabilityProvider(spec, plugin, source, distribution, version, repository, commit)
            bucket = self._providers.setdefault(spec.id, [])
            if provider not in bucket:
                bucket.append(provider)

    def capability_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def providers(self, capability_id: str) -> tuple[CapabilityProvider, ...]:
        return tuple(
            sorted(
                self._providers.get(capability_id, ()),
                key=lambda p: (p.capability.cost_weight, p.plugin, p.capability.task),
            )
        )

    def resolve(self, capability_id: str, *, preferred_plugin: str | None = None) -> CapabilityProvider:
        providers = list(self.providers(capability_id))
        if preferred_plugin is not None:
            providers = [p for p in providers if p.plugin == preferred_plugin]
        if not providers:
            providers = [
                provider
                for key in self._providers
                if key.endswith(capability_id)
                for provider in self.providers(key)
                if preferred_plugin is None or provider.plugin == preferred_plugin
            ]
        if not providers:
            raise KeyError(f"No provider for capability {capability_id!r}")
        return providers[0]

    def to_dict(self) -> dict[str, Any]:
        plugins: dict[str, list[str]] = {}
        for capability_id in self.capability_ids():
            for provider in self.providers(capability_id):
                plugins.setdefault(provider.plugin, []).append(capability_id)
        return {
            "capabilities": {
                capability_id: [p.to_dict() for p in self.providers(capability_id)]
                for capability_id in self.capability_ids()
            },
            "plugins": {name: sorted(ids) for name, ids in sorted(plugins.items())},
            "edges": [
                {"relation": "IMPLEMENTS", "plugin": provider.plugin, "capability": capability_id}
                for capability_id in self.capability_ids()
                for provider in self.providers(capability_id)
            ],
        }


def specs_from_plugin(plugin: Any) -> tuple[CapabilitySpec, ...]:
    """Read rich specs when available, else lift legacy string capabilities."""
    rich = getattr(plugin, "capability_specs", None)
    if callable(rich):
        specs = tuple(rich())
        if not all(isinstance(item, CapabilitySpec) for item in specs):
            raise TypeError("capability_specs() must return CapabilitySpec objects")
        return specs
    raw: Sequence[str] = plugin.capabilities()
    return tuple(
        CapabilitySpec(
            id=f"{plugin.name}.{name}",
            task=str(name),
            description=f"Legacy capability exposed by {plugin.name}",
        )
        for name in raw
    )
