"""Composable runtime for executing Tristan Python plugins together."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import metadata
from time import perf_counter
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

from .capabilities import CapabilityGraph, specs_from_plugin
from .capsule import ExecutionCapsule
from .policy import PolicyContext, PolicyKernel
from .tir import Provenance, TristanArtifact

ENTRYPOINT_GROUP = "tristan.plugins"


@runtime_checkable
class TristanPlugin(Protocol):
    name: str

    def capabilities(self) -> Sequence[str]: ...
    def run(self, task: str, payload: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True, slots=True)
class PluginInfo:
    name: str
    source: str
    capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PipelineStep:
    plugin: str
    task: str


@dataclass(frozen=True, slots=True)
class CapabilityExecution:
    provider: str
    capability: str
    task: str
    output: Any
    artifact: TristanArtifact
    capsule: ExecutionCapsule

    def to_dict(self) -> dict[str, Any]:
        return {"provider": self.provider, "capability": self.capability, "task": self.task, "output": self.output, "artifact": self.artifact.to_dict(), "capsule": self.capsule.to_dict()}


class TristanRuntime:
    """Discover, register, compose, and audit plugins without hidden network actions."""

    def __init__(self, *, auto_discover: bool = True):
        self._plugins: dict[str, tuple[str, TristanPlugin]] = {}
        self._policy = PolicyKernel()
        if auto_discover:
            self.discover()

    @staticmethod
    def _entry_points() -> Iterable[metadata.EntryPoint]:
        points = metadata.entry_points()
        if hasattr(points, "select"):
            return points.select(group=ENTRYPOINT_GROUP)
        return points.get(ENTRYPOINT_GROUP, ())  # pragma: no cover

    @staticmethod
    def _normalize_plugin(loaded: Any) -> TristanPlugin:
        candidate = loaded
        if isinstance(candidate, type):
            candidate = candidate()
        elif callable(candidate) and not hasattr(candidate, "run"):
            candidate = candidate()
        if not hasattr(candidate, "name") or not callable(getattr(candidate, "run", None)):
            raise TypeError("Tristan plugin must expose a name and run(task, payload).")
        if not callable(getattr(candidate, "capabilities", None)):
            raise TypeError("Tristan plugin must expose capabilities().")
        return candidate

    def discover(self) -> tuple[PluginInfo, ...]:
        for entry_point in self._entry_points():
            try:
                plugin = self._normalize_plugin(entry_point.load())
            except Exception:
                continue
            self.register(plugin, source=f"entrypoint:{entry_point.value}", replace=True)
        return self.plugins()

    def register(self, plugin: TristanPlugin, *, source: str = "manual", replace: bool = False) -> None:
        normalized = self._normalize_plugin(plugin)
        if normalized.name in self._plugins and not replace:
            raise ValueError(f"Plugin already registered: {normalized.name}")
        self._plugins[normalized.name] = (source, normalized)

    def plugins(self) -> tuple[PluginInfo, ...]:
        return tuple(PluginInfo(name, source, tuple(str(item) for item in plugin.capabilities())) for name, (source, plugin) in sorted(self._plugins.items()))

    def capability_graph(self) -> CapabilityGraph:
        graph = CapabilityGraph()
        for name, (source, plugin) in sorted(self._plugins.items()):
            graph.add(plugin=name, source=source, specs=specs_from_plugin(plugin))
        return graph

    def run(self, plugin_name: str, task: str, payload: Mapping[str, Any] | None = None) -> Any:
        if plugin_name not in self._plugins:
            raise KeyError(f"Plugin {plugin_name!r} is not registered. Available: {', '.join(sorted(self._plugins)) or '<none>'}")
        _, plugin = self._plugins[plugin_name]
        return plugin.run(task, dict(payload or {}))

    def execute_capability(self, capability_id: str, payload: Mapping[str, Any] | None = None, *, preferred_plugin: str | None = None, policy_context: PolicyContext | None = None) -> CapabilityExecution:
        provider = self.capability_graph().resolve(capability_id, preferred_plugin=preferred_plugin)
        decision = self._policy.require(provider.capability, policy_context)
        source, _ = self._plugins[provider.plugin]
        data = dict(payload or {})
        started_at = datetime.now(timezone.utc)
        start = perf_counter()
        output = self.run(provider.plugin, provider.capability.task, data)
        duration_ms = (perf_counter() - start) * 1000.0
        artifact = TristanArtifact.build(kind=provider.capability.output_kind, payload=output, provenance=Provenance(source=provider.plugin, operation=provider.capability.id), oak_status="EXECUTED_UNVERIFIED")
        capsule = ExecutionCapsule.build(plugin=provider.plugin, capability=provider.capability.id, task=provider.capability.task, payload=data, output=output, started_at=started_at, duration_ms=duration_ms, source=source, policy=decision.to_dict())
        return CapabilityExecution(provider.plugin, provider.capability.id, provider.capability.task, output, artifact, capsule)

    def pipeline(self, steps: Iterable[PipelineStep | tuple[str, str]], payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        current: Mapping[str, Any] = dict(payload or {})
        history: list[dict[str, Any]] = []
        for raw_step in steps:
            step = raw_step if isinstance(raw_step, PipelineStep) else PipelineStep(*raw_step)
            result = self.run(step.plugin, step.task, current)
            history.append({"plugin": step.plugin, "task": step.task, "result": result})
            current = result if isinstance(result, Mapping) else {"value": result}
        return {"result": dict(current), "history": history}

    def capability_pipeline(self, capability_ids: Iterable[str], payload: Mapping[str, Any] | None = None, *, policy_context: PolicyContext | None = None) -> dict[str, Any]:
        current: Mapping[str, Any] = dict(payload or {})
        history: list[dict[str, Any]] = []
        for capability_id in capability_ids:
            execution = self.execute_capability(capability_id, current, policy_context=policy_context)
            history.append(execution.to_dict())
            current = execution.output if isinstance(execution.output, Mapping) else {"value": execution.output}
        return {"result": dict(current), "history": history}
