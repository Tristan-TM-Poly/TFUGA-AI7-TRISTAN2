"""Typed bounded benchmark contracts for Omega Compute Physics R0.5.

The module provides an OAK gate for dynamic benchmarking. It is deliberately
conservative: process timeouts and isolated interpreters are *not* security
sandboxes. Untrusted code, network use, credentials, destructive I/O and
external side effects are rejected unless a higher-level reviewed adapter
handles them outside this runner.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class BenchmarkRisk:
    network: bool = False
    credentials: bool = False
    destructive_io: bool = False
    external_side_effects: bool = False
    privileged_operations: bool = False

    def blocked_reasons(self) -> tuple[str, ...]:
        return tuple(name for name, value in asdict(self).items() if value)


@dataclass(frozen=True)
class InputAxis:
    name: str
    values: tuple[float, ...]
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("axis name cannot be empty")
        if not self.values:
            raise ValueError(f"axis {self.name!r} needs at least one value")


@dataclass(frozen=True)
class BenchmarkContract:
    contract_id: str
    repository: str
    commit_sha: str
    module: str
    callable_name: str
    axes: tuple[InputAxis, ...]
    fixture: str
    repeats: int = 5
    warmups: int = 1
    timeout_s: float = 10.0
    max_cases: int = 128
    trusted_checkout: bool = False
    risk: BenchmarkRisk = field(default_factory=BenchmarkRisk)
    environment_allowlist: tuple[str, ...] = ()
    status: str = "benchmark-contract-candidate"

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.contract_id:
            errors.append("contract_id missing")
        if not self.repository or not self.commit_sha:
            errors.append("repository and pinned commit_sha are required")
        if not self.module or not self.callable_name:
            errors.append("module and callable_name are required")
        if not self.fixture:
            errors.append("a deterministic fixture identifier is required")
        if self.repeats < 1 or self.repeats > 100:
            errors.append("repeats must be in [1, 100]")
        if self.warmups < 0 or self.warmups > 20:
            errors.append("warmups must be in [0, 20]")
        if self.timeout_s <= 0 or self.timeout_s > 300:
            errors.append("timeout_s must be in (0, 300]")
        cases = 1
        for axis in self.axes:
            cases *= len(axis.values)
        if cases > self.max_cases:
            errors.append(f"design has {cases} cases > max_cases={self.max_cases}")
        if not self.trusted_checkout:
            errors.append("trusted_checkout must be explicitly true for dynamic execution")
        for reason in self.risk.blocked_reasons():
            errors.append(f"blocked risk: {reason}")
        return tuple(errors)

    @property
    def executable(self) -> bool:
        return not self.validate()

    def certificate(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "executable": self.executable,
            "validation_errors": list(self.validate()),
            "oak_warning": (
                "This contract is a policy gate, not a security sandbox. Dynamic execution "
                "must occur only in an appropriate trusted or externally sandboxed environment."
            ),
        }


def load_contract(path: str | Path) -> BenchmarkContract:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    axes = tuple(
        InputAxis(
            name=row["name"],
            values=tuple(float(v) for v in row["values"]),
            description=row.get("description", ""),
        )
        for row in payload.get("axes", [])
    )
    risk = BenchmarkRisk(**payload.get("risk", {}))
    return BenchmarkContract(
        contract_id=payload["contract_id"],
        repository=payload["repository"],
        commit_sha=payload["commit_sha"],
        module=payload["module"],
        callable_name=payload["callable_name"],
        axes=axes,
        fixture=payload["fixture"],
        repeats=int(payload.get("repeats", 5)),
        warmups=int(payload.get("warmups", 1)),
        timeout_s=float(payload.get("timeout_s", 10.0)),
        max_cases=int(payload.get("max_cases", 128)),
        trusted_checkout=bool(payload.get("trusted_checkout", False)),
        risk=risk,
        environment_allowlist=tuple(payload.get("environment_allowlist", [])),
    )


def gate_contract(contract: BenchmarkContract) -> dict[str, Any]:
    """Return a machine-readable go/no-go decision without executing code."""
    errors = contract.validate()
    return {
        "contract_id": contract.contract_id,
        "decision": "allow" if not errors else "block",
        "reasons": list(errors),
        "status": "oak-dynamic-benchmark-gate",
        "oak_warning": "ALLOW means policy-compatible, not sandboxed or risk-free.",
    }
