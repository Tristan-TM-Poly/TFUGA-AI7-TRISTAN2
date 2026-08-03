"""Transparent finite-matrix assumptions and numerical checks."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping
import numpy as np
import numpy.typing as npt

ArrayLike = npt.ArrayLike


class AssumptionKind(str, Enum):
    SQUARE = "square"
    SYMMETRIC = "symmetric"
    SKEW_SYMMETRIC = "skew_symmetric"
    HERMITIAN = "hermitian"
    UNITARY = "unitary"
    ORTHOGONAL = "orthogonal"
    PROJECTION = "projection"
    INVOLUTION = "involution"
    INVERTIBLE = "invertible"
    NORMAL = "normal"
    POSITIVE_SEMIDEFINITE = "positive_semidefinite"
    COMMUTING = "commuting"


@dataclass(frozen=True, order=True)
class Assumption:
    kind: AssumptionKind
    targets: tuple[str, ...]
    tolerance: float = 1e-9

    def __post_init__(self) -> None:
        required = 2 if self.kind == AssumptionKind.COMMUTING else 1
        if len(self.targets) != required:
            raise ValueError(f"{self.kind.value} requires {required} target(s)")
        if self.tolerance <= 0:
            raise ValueError("assumption tolerance must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "targets": list(self.targets),
            "tolerance": self.tolerance,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Assumption":
        return cls(
            AssumptionKind(str(payload["kind"])),
            tuple(str(x) for x in payload["targets"]),
            float(payload.get("tolerance", 1e-9)),
        )

    def check(self, environment: Mapping[str, ArrayLike]) -> tuple[bool, float]:
        matrices = [np.asarray(environment[name], dtype=np.complex128) for name in self.targets]
        if any(value.ndim != 2 or not np.all(np.isfinite(value)) for value in matrices):
            return False, float("inf")
        a = matrices[0]
        if self.kind == AssumptionKind.SQUARE:
            return a.shape[0] == a.shape[1], 0.0 if a.shape[0] == a.shape[1] else 1.0
        if a.shape[0] != a.shape[1]:
            return False, float("inf")
        identity = np.eye(a.shape[0], dtype=np.complex128)
        scale = max(float(np.linalg.norm(a)), 1.0)

        if self.kind == AssumptionKind.SYMMETRIC:
            residual = np.linalg.norm(a - a.T) / scale
        elif self.kind == AssumptionKind.SKEW_SYMMETRIC:
            residual = np.linalg.norm(a + a.T) / scale
        elif self.kind == AssumptionKind.HERMITIAN:
            residual = np.linalg.norm(a - a.conj().T) / scale
        elif self.kind == AssumptionKind.UNITARY:
            residual = np.linalg.norm(a.conj().T @ a - identity) / max(np.sqrt(a.shape[0]), 1.0)
        elif self.kind == AssumptionKind.ORTHOGONAL:
            residual = np.linalg.norm(a.T @ a - identity) / max(np.sqrt(a.shape[0]), 1.0)
        elif self.kind == AssumptionKind.PROJECTION:
            residual = np.linalg.norm(a @ a - a) / scale
        elif self.kind == AssumptionKind.INVOLUTION:
            residual = np.linalg.norm(a @ a - identity) / max(np.sqrt(a.shape[0]), 1.0)
        elif self.kind == AssumptionKind.INVERTIBLE:
            smallest = float(np.min(np.linalg.svd(a, compute_uv=False), initial=0.0))
            residual = 0.0 if smallest > self.tolerance else self.tolerance - smallest
        elif self.kind == AssumptionKind.NORMAL:
            residual = np.linalg.norm(a @ a.conj().T - a.conj().T @ a) / max(scale**2, 1.0)
        elif self.kind == AssumptionKind.POSITIVE_SEMIDEFINITE:
            hermitian = 0.5 * (a + a.conj().T)
            minimum = float(np.min(np.linalg.eigvalsh(hermitian), initial=0.0))
            residual = max(0.0, -minimum)
        elif self.kind == AssumptionKind.COMMUTING:
            b = matrices[1]
            if b.shape != a.shape:
                return False, float("inf")
            residual = np.linalg.norm(a @ b - b @ a) / max(
                float(np.linalg.norm(a) * np.linalg.norm(b)), 1.0
            )
        else:
            raise ValueError(f"unknown assumption {self.kind}")
        value = float(residual)
        return value <= self.tolerance, value


def audit_assumptions(
    assumptions: tuple[Assumption, ...],
    environment: Mapping[str, ArrayLike],
) -> tuple[bool, tuple[dict[str, Any], ...]]:
    records: list[dict[str, Any]] = []
    passed = True
    for assumption in assumptions:
        ok, residual = assumption.check(environment)
        passed &= ok
        records.append({**assumption.to_dict(), "passed": ok, "residual": residual})
    return passed, tuple(records)
