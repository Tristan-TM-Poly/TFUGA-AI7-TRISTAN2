"""Reproducible execution capsules for Tristan runtime calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
from typing import Any

from .tir import stable_digest


def _safe(value: Any) -> Any:
    try:
        json.dumps(value)
    except TypeError:
        if hasattr(value, "to_dict"):
            return value.to_dict()
        if isinstance(value, dict):
            return {str(k): _safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_safe(v) for v in value]
        return repr(value)
    return value


@dataclass(frozen=True, slots=True)
class ExecutionCapsule:
    capsule_id: str
    plugin: str
    capability: str
    task: str
    input_digest: str
    output_digest: str
    started_at: str
    duration_ms: float
    python: str
    platform: str
    source: str
    policy: dict[str, Any]

    @classmethod
    def build(cls, *, plugin: str, capability: str, task: str, payload: Any, output: Any, started_at: datetime, duration_ms: float, source: str, policy: dict[str, Any]) -> "ExecutionCapsule":
        input_digest = stable_digest(payload)
        output_digest = stable_digest(output)
        capsule_id = stable_digest({"plugin": plugin, "capability": capability, "task": task, "input_digest": input_digest, "output_digest": output_digest, "source": source})
        return cls(
            capsule_id=f"capsule:{capsule_id[:20]}",
            plugin=plugin,
            capability=capability,
            task=task,
            input_digest=input_digest,
            output_digest=output_digest,
            started_at=started_at.astimezone(timezone.utc).isoformat(),
            duration_ms=round(duration_ms, 3),
            python=sys.version.split()[0],
            platform=platform.platform(),
            source=source,
            policy=policy,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, directory: str | Path, *, payload: Any, output: Any) -> Path:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        (root / "manifest.json").write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        (root / "input.json").write_text(json.dumps(_safe(payload), indent=2, ensure_ascii=False), encoding="utf-8")
        (root / "output.json").write_text(json.dumps(_safe(output), indent=2, ensure_ascii=False), encoding="utf-8")
        return root
