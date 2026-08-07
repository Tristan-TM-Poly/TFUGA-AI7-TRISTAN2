"""Composable runtime for executing Tristan Python plugins together."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

ENTRYPOINT_GROUP = "tristan.plugins"


@runtime_checkable
class TristanPlugin(Protocol):
    """Minimal contract implemented by every executable Tristan system."""

    name: str

    def capabilities(self) -> Sequence[str]:
        ...

    def run(self, task: str, payload: Mapping[str, Any]) -> Any:
        ...


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


class TristanRuntime:
    """Discover, register, and compose plugins without hidden network actions."""

    def __init__(self, *, auto_discover: bool = True):
        self._plugins: dict[str, tuple[str, TristanPlugin]] = {}
        if auto_discover:
            self.discover()

    @staticmethod
    def _entry_points() -> Iterable[metadata.EntryPoint]:
        points = metadata.entry_points()
        if hasattr(points, "select"):
            return points.select(group=ENTRYPOINT_GROUP)
        return points.get(ENTRYPOINT_GROUP, ())  # pragma: no cover - Python 3.10 compatibility

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
                # Discovery is resilient: one broken optional package must not
                # make every other Tristan system unavailable.
                continue
            self.register(plugin, source=f"entrypoint:{entry_point.value}", replace=True)
        return self.plugins()

    def register(self, plugin: TristanPlugin, *, source: str = "manual", replace: bool = False) -> None:
        normalized = self._normalize_plugin(plugin)
        if normalized.name in self._plugins and not replace:
            raise ValueError(f"Plugin already registered: {normalized.name}")
        self._plugins[normalized.name] = (source, normalized)

    def plugins(self) -> tuple[PluginInfo, ...]:
        infos = []
        for name, (source, plugin) in sorted(self._plugins.items()):
            infos.append(
                PluginInfo(
                    name=name,
                    source=source,
                    capabilities=tuple(str(item) for item in plugin.capabilities()),
                )
            )
        return tuple(infos)

    def run(self, plugin_name: str, task: str, payload: Mapping[str, Any] | None = None) -> Any:
        if plugin_name not in self._plugins:
            raise KeyError(
                f"Plugin {plugin_name!r} is not registered. "
                f"Available: {', '.join(sorted(self._plugins)) or '<none>'}"
            )
        _, plugin = self._plugins[plugin_name]
        return plugin.run(task, dict(payload or {}))

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
