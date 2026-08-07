"""Bounded subprocess execution for Tristan capabilities.

This is a user-space isolation layer, not a certified security boundary. It gives
capabilities a fresh process, timeout, temporary working directory, reduced
environment, optional POSIX resource ceilings, and an explicit network guard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SandboxResult:
    capability: str
    output: Any
    stdout: str
    stderr: str
    returncode: int
    timeout_seconds: float
    memory_mb: int
    isolation_strength: str = "USER_SPACE_BOUNDED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionSandbox:
    def __init__(self, *, timeout_seconds: float = 10.0, memory_mb: int = 512):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if memory_mb <= 0:
            raise ValueError("memory_mb must be positive")
        self.timeout_seconds = float(timeout_seconds)
        self.memory_mb = int(memory_mb)

    def run(
        self,
        capability: str,
        payload: Mapping[str, Any] | None = None,
        *,
        allowed_permissions: tuple[str, ...] = ("PURE",),
    ) -> SandboxResult:
        request = {
            "capability": capability,
            "payload": dict(payload or {}),
            "allowed_permissions": list(allowed_permissions),
            "memory_mb": self.memory_mb,
        }
        with tempfile.TemporaryDirectory(prefix="tristan-sandbox-") as workdir:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "PYTHONIOENCODING": "utf-8",
                "TRISTAN_SANDBOX_WORKER": "1",
            }
            completed = subprocess.run(
                [sys.executable, "-m", "omega_ai_tristan_lab.sandbox_worker"],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                cwd=workdir,
                env=env,
                timeout=self.timeout_seconds,
                check=False,
            )
        if completed.returncode != 0:
            raise RuntimeError(
                f"Sandbox capability {capability!r} failed with code {completed.returncode}: {completed.stderr.strip()}"
            )
        response = json.loads(completed.stdout)
        return SandboxResult(
            capability=capability,
            output=response["output"],
            stdout=response.get("worker_stdout", ""),
            stderr=completed.stderr,
            returncode=completed.returncode,
            timeout_seconds=self.timeout_seconds,
            memory_mb=self.memory_mb,
        )
