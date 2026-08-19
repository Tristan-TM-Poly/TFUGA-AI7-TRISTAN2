"""Composable runtime for executing Tristan capability plugins together."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import metadata
from time import perf_counter
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

from .capabilities import CapabilityGraph, specs_from_plugin
from .capsule import ExecutionCapsule
from .discovery import DiscoveryFailure, DiscoveryReport
from .planner import PipelineCompiler
from .policy import PolicyContext, PolicyKernel
from .provenance_runtime import DistributionFingerprint, fingerprint_distribution
from .schemas import SchemaGraph, specs_from_plugin as schema_specs_from_plugin
from .tir import Provenance, TristanArtifact

ENTRYPOINT_GROUP = "tristan.plugins"
DISCOVERY_MODES = {"lenient", "strict", "oak-strict"}


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
    distribution: str = ""
    version: str = ""
    repository: str = ""
    commit: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PluginRegistration:
    source: str
    plugin: TristanPlugin
    fingerprint: DistributionFingerprint


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
        return {
            "provider": self.provider,
            "capability": self.capability,
            "task": self.task,
            "output": self.output,
            "artifact": self.artifact.to_dict(),
            "capsule": self.capsule.to_dict(),
        }


class TristanRuntime:
    """Discover, register, compose, validate and audit capability providers."""

    def __init__(
        self,
        *,
        auto_discover: bool = True,
        discovery_mode: str = "lenient",
        expected_plugins: Iterable[str] = (),
    ):
        if discovery_mode not in DISCOVERY_MODES:
            raise ValueError(f"discovery_mode must be one of {sorted(DISCOVERY_MODES)}")
        self._plugins: dict[str, PluginRegistration] = {}
        self._policy = PolicyKernel()
        self._discovery_mode = discovery_mode
        self._expected_plugins = tuple(sorted(set(map(str, expected_plugins))))
        self._discovery_failures: list[DiscoveryFailure] = []
        self._last_discovery_report = DiscoveryReport((), (), self._expected_plugins, discovery_mode)
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

    @staticmethod
    def _entrypoint_fingerprint(entry_point: metadata.EntryPoint) -> DistributionFingerprint:
        dist = getattr(entry_point, "dist", None)
        name = getattr(dist, "name", "") if dist is not None else ""
        fp = fingerprint_distribution(name)
        if dist is not None and not fp.version:
            fp = DistributionFingerprint(
                distribution=name,
                version=getattr(dist, "version", ""),
                repository=fp.repository,
                commit=fp.commit,
                install_source=fp.install_source,
                wheel_sha256=fp.wheel_sha256,
            )
        return fp

    def discover(self) -> tuple[PluginInfo, ...]:
        self._discovery_failures.clear()
        for entry_point in self._entry_points():
            fp = self._entrypoint_fingerprint(entry_point)
            try:
                plugin = self._normalize_plugin(entry_point.load())
                self.register(
                    plugin,
                    source=f"entrypoint:{entry_point.value}",
                    replace=True,
                    fingerprint=fp,
                )
            except Exception as exc:
                self._discovery_failures.append(
                    DiscoveryFailure(
                        entrypoint=str(entry_point.name),
                        value=str(entry_point.value),
                        distribution=fp.distribution,
                        version=fp.version,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )
        loaded = tuple(info.name for info in self.plugins())
        expected_missing = tuple(name for name in self._expected_plugins if name not in loaded)
        report = DiscoveryReport(loaded, tuple(self._discovery_failures), expected_missing, self._discovery_mode)
        self._last_discovery_report = report
        if self._discovery_mode == "strict" and report.failed:
            raise RuntimeError(f"Plugin discovery failed: {report.to_dict()}")
        if self._discovery_mode == "oak-strict" and not report.ok:
            raise RuntimeError(f"OAK-strict plugin discovery failed: {report.to_dict()}")
        return self.plugins()

    def discovery_report(self) -> DiscoveryReport:
        return self._last_discovery_report

    def register(
        self,
        plugin: TristanPlugin,
        *,
        source: str = "manual",
        replace: bool = False,
        fingerprint: DistributionFingerprint | None = None,
    ) -> None:
        normalized = self._normalize_plugin(plugin)
        if normalized.name in self._plugins and not replace:
            raise ValueError(f"Plugin already registered: {normalized.name}")
        fp = fingerprint or fingerprint_distribution(getattr(normalized, "distribution", normalized.name))
        if not fp.version and getattr(normalized, "version", ""):
            fp = DistributionFingerprint(
                distribution=fp.distribution or getattr(normalized, "distribution", normalized.name),
                version=str(getattr(normalized, "version", "")),
                repository=fp.repository,
                commit=fp.commit,
                install_source=fp.install_source,
                wheel_sha256=fp.wheel_sha256,
            )
        self._plugins[normalized.name] = PluginRegistration(source, normalized, fp)

    def plugins(self) -> tuple[PluginInfo, ...]:
        rows: list[PluginInfo] = []
        for name, registration in sorted(self._plugins.items()):
            fp = registration.fingerprint
            rows.append(
                PluginInfo(
                    name=name,
                    source=registration.source,
                    capabilities=tuple(str(item) for item in registration.plugin.capabilities()),
                    distribution=fp.distribution,
                    version=fp.version,
                    repository=fp.repository,
                    commit=fp.commit,
                )
            )
        return tuple(rows)

    def schema_graph(self) -> SchemaGraph:
        graph = SchemaGraph()
        for registration in self._plugins.values():
            for schema in schema_specs_from_plugin(registration.plugin):
                graph.register(schema)
        return graph

    def capability_graph(self) -> CapabilityGraph:
        graph = CapabilityGraph()
        for name, registration in sorted(self._plugins.items()):
            fp = registration.fingerprint
            graph.add(
                plugin=name,
                source=registration.source,
                specs=specs_from_plugin(registration.plugin),
                distribution=fp.distribution,
                version=fp.version,
                repository=fp.repository,
                commit=fp.commit,
            )
        return graph

    def pipeline_compiler(self) -> PipelineCompiler:
        return PipelineCompiler(self.capability_graph(), self.schema_graph())

    def run(self, plugin_name: str, task: str, payload: Mapping[str, Any] | None = None) -> Any:
        if plugin_name not in self._plugins:
            raise KeyError(
                f"Plugin {plugin_name!r} is not registered. "
                f"Available: {', '.join(sorted(self._plugins)) or '<none>'}"
            )
        return self._plugins[plugin_name].plugin.run(task, dict(payload or {}))

    def execute_capability(
        self,
        capability_id: str,
        payload: Mapping[str, Any] | None = None,
        *,
        preferred_plugin: str | None = None,
        policy_context: PolicyContext | None = None,
        parent_artifacts: Iterable[str] = (),
    ) -> CapabilityExecution:
        provider = self.capability_graph().resolve(capability_id, preferred_plugin=preferred_plugin)
        decision = self._policy.require(provider.capability, policy_context)
        data = dict(payload or {})
        schemas = self.schema_graph()
        input_errors = schemas.validate(provider.capability.input_schema, data)
        if input_errors:
            raise ValueError(f"Input schema {provider.capability.input_schema!r} rejected payload: {'; '.join(input_errors)}")

        registration = self._plugins[provider.plugin]
        fp = registration.fingerprint
        started_at = datetime.now(timezone.utc)
        start = perf_counter()
        output = self.run(provider.plugin, provider.capability.task, data)
        duration_ms = (perf_counter() - start) * 1000.0

        output_errors = schemas.validate(provider.capability.output_schema, output)
        if output_errors:
            raise ValueError(
                f"Output schema {provider.capability.output_schema!r} rejected result from "
                f"{provider.capability.id!r}: {'; '.join(output_errors)}"
            )

        artifact = TristanArtifact.build(
            kind=provider.capability.output_kind,
            payload=output,
            provenance=Provenance(
                source=provider.plugin,
                version=fp.version,
                operation=provider.capability.id,
                parents=tuple(parent_artifacts),
                commit=fp.commit,
                distribution=fp.distribution,
                repository=fp.repository,
                install_source=fp.install_source,
                wheel_sha256=fp.wheel_sha256,
            ),
            oak_status="EXECUTED_UNVERIFIED",
        )
        capsule = ExecutionCapsule.build(
            plugin=provider.plugin,
            capability=provider.capability.id,
            task=provider.capability.task,
            payload=data,
            output=output,
            started_at=started_at,
            duration_ms=duration_ms,
            source=registration.source,
            policy=decision.to_dict(),
        )
        return CapabilityExecution(
            provider.plugin,
            provider.capability.id,
            provider.capability.task,
            output,
            artifact,
            capsule,
        )

    def execute_sandboxed(
        self,
        capability_id: str,
        payload: Mapping[str, Any] | None = None,
        *,
        timeout_seconds: float = 10.0,
        memory_mb: int = 512,
        allowed_permissions: tuple[str, ...] = ("PURE",),
    ) -> Any:
        from .sandbox import ExecutionSandbox
        return ExecutionSandbox(timeout_seconds=timeout_seconds, memory_mb=memory_mb).run(
            capability_id,
            payload,
            allowed_permissions=allowed_permissions,
        )

    def pipeline(
        self,
        steps: Iterable[PipelineStep | tuple[str, str]],
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        current: Mapping[str, Any] = dict(payload or {})
        history: list[dict[str, Any]] = []
        for raw_step in steps:
            step = raw_step if isinstance(raw_step, PipelineStep) else PipelineStep(*raw_step)
            result = self.run(step.plugin, step.task, current)
            history.append({"plugin": step.plugin, "task": step.task, "result": result})
            current = result if isinstance(result, Mapping) else {"value": result}
        return {"result": dict(current), "history": history}

    def capability_pipeline(
        self,
        capability_ids: Iterable[str],
        payload: Mapping[str, Any] | None = None,
        *,
        policy_context: PolicyContext | None = None,
        initial_schema: str = "tristan.any",
    ) -> dict[str, Any]:
        ids = tuple(capability_ids)
        plan = self.pipeline_compiler().compile(ids, initial_schema=initial_schema)
        current: Mapping[str, Any] = dict(payload or {})
        history: list[dict[str, Any]] = []
        parent_artifacts: tuple[str, ...] = ()
        for capability_id in ids:
            execution = self.execute_capability(
                capability_id,
                current,
                policy_context=policy_context,
                parent_artifacts=parent_artifacts,
            )
            history.append(execution.to_dict())
            parent_artifacts = (execution.artifact.digest,)
            current = execution.output if isinstance(execution.output, Mapping) else {"value": execution.output}
        return {"result": dict(current), "history": history, "plan": plan.to_dict()}
