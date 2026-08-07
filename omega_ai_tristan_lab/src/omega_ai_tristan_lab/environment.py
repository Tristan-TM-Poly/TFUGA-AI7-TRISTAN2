"""Runtime environment identity and compatibility matrix contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import platform
import sys
from typing import Any


@dataclass(frozen=True, slots=True)
class EnvironmentTarget:
    implementation: str
    python: str
    os: str
    architecture: str

    @classmethod
    def current(cls) -> "EnvironmentTarget":
        return cls(
            implementation=platform.python_implementation(),
            python=f"{sys.version_info.major}.{sys.version_info.minor}",
            os=platform.system().lower(),
            architecture=platform.machine().lower(),
        )

    @property
    def key(self) -> str:
        return f"{self.implementation.lower()}-{self.python}-{self.os}-{self.architecture}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["key"] = self.key
        return data


class EnvironmentMatrix:
    """Declared target matrix; CI decides which targets have actual receipts."""

    def __init__(self) -> None:
        self.targets = tuple(
            EnvironmentTarget("CPython", python, os_name, arch)
            for python in ("3.10", "3.11", "3.12")
            for os_name, arch in (
                ("linux", "x86_64"),
                ("windows", "amd64"),
                ("darwin", "arm64"),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        current = EnvironmentTarget.current()
        return {
            "current": current.to_dict(),
            "declared_targets": [target.to_dict() for target in self.targets],
            "note": "Declared compatibility targets are not verification receipts; CI results are required per target.",
        }
