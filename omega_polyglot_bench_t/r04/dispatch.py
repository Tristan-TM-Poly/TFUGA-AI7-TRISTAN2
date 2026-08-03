"""Contextual selection from a previously measured R0.4 profile."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .native import KernelLibrary


@dataclass(frozen=True)
class DispatchDecision:
    algorithm: str
    requested_size: int
    trained_size: int
    candidate_id: str
    reason: str


class AutotunedDispatcher:
    def __init__(self, report_path: Path, build_dir: Path | None = None) -> None:
        payload = json.loads(report_path.read_text())
        self.report_path = report_path
        self.build_dir = build_dir
        self._champions = payload.get("champions", [])
        self._libraries: dict[tuple[str, str], KernelLibrary] = {}

    def decide(self, algorithm: str, size: int) -> DispatchDecision:
        candidates = [item for item in self._champions if item["algorithm"] == algorithm]
        if not candidates:
            raise LookupError(f"no champion for algorithm {algorithm!r}")
        chosen = min(candidates, key=lambda item: (abs(int(item["size"]) - size), int(item["size"])))
        return DispatchDecision(
            algorithm=algorithm,
            requested_size=size,
            trained_size=int(chosen["size"]),
            candidate_id=chosen["candidate_id"],
            reason="nearest measured size on the same hardware profile",
        )

    def library_for(self, decision: DispatchDecision) -> tuple[KernelLibrary, str]:
        backend, profile, variant = decision.candidate_id.split(":", 2)
        key = (backend, profile)
        if key not in self._libraries:
            self._libraries[key] = KernelLibrary(backend, profile, self.build_dir)
        return self._libraries[key], variant

    def execute_affine(self, x: Any, y: Any, scalar: float, output: Any | None = None) -> tuple[Any, DispatchDecision]:
        decision = self.decide("affine", len(x))
        library, variant = self.library_for(decision)
        result = library.prepare_affine(variant, x, y, output).run(scalar)
        return result, decision
