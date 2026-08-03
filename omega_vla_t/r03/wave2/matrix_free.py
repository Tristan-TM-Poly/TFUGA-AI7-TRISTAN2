"""Bounded matrix-free operator semantics for Ω-VLA Wave 2.

The implementation models finite-dimensional actions without requiring a dense
matrix to be stored. It deliberately rejects ambiguous shapes and preserves
resource envelopes when materialization is requested.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Iterable

import numpy as np
import numpy.typing as npt

from ..types import MathType, ScalarSystem, TypeSystemError, UnitDimension

Array = npt.NDArray[np.complex128]
Matvec = Callable[[Array], npt.ArrayLike]


class MatrixFreeError(ValueError):
    pass


@dataclass(frozen=True)
class MatrixFreeAudit:
    name: str
    shape: tuple[int, int]
    trials: int
    linearity_residual: float
    adjoint_residual: float | None
    norm_upper_estimate: float
    finite: bool
    passed: bool
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MatrixFreeOperator:
    """Finite-dimensional matrix-free linear operator.

    ``matvec`` computes A x. ``rmatvec`` computes A* y when available. Callables
    are runtime objects and therefore are not directly serialized; the digest
    covers declared metadata only.
    """

    name: str
    codomain_dimension: int
    domain_dimension: int
    matvec: Matvec
    rmatvec: Matvec | None = None
    scalar_system: ScalarSystem = ScalarSystem.COMPLEX
    units: UnitDimension = UnitDimension()
    domain_id: str | None = None
    codomain_id: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise MatrixFreeError("matrix-free operators require a non-empty name")
        if self.codomain_dimension <= 0 or self.domain_dimension <= 0:
            raise MatrixFreeError("matrix-free dimensions must be positive")
        if not callable(self.matvec):
            raise MatrixFreeError("matvec must be callable")
        if self.rmatvec is not None and not callable(self.rmatvec):
            raise MatrixFreeError("rmatvec must be callable when supplied")

    @property
    def shape(self) -> tuple[int, int]:
        return (self.codomain_dimension, self.domain_dimension)

    @property
    def math_type(self) -> MathType:
        return MathType.linear_operator(
            self.codomain_dimension,
            self.domain_dimension,
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.domain_id,
            codomain_id=self.codomain_id,
        )

    def apply(self, vector: npt.ArrayLike) -> Array:
        x = np.asarray(vector, dtype=np.complex128)
        if x.shape != (self.domain_dimension,):
            raise MatrixFreeError(
                f"{self.name} expected vector shape {(self.domain_dimension,)}, got {x.shape}"
            )
        result = np.asarray(self.matvec(x), dtype=np.complex128)
        if result.shape != (self.codomain_dimension,):
            raise MatrixFreeError(
                f"{self.name}.matvec returned {result.shape}, expected {(self.codomain_dimension,)}"
            )
        if not np.all(np.isfinite(result)):
            raise MatrixFreeError("matrix-free action produced non-finite values")
        return result

    def apply_adjoint(self, vector: npt.ArrayLike) -> Array:
        if self.rmatvec is None:
            raise MatrixFreeError(f"{self.name} has no declared adjoint action")
        y = np.asarray(vector, dtype=np.complex128)
        if y.shape != (self.codomain_dimension,):
            raise MatrixFreeError(
                f"adjoint expected vector shape {(self.codomain_dimension,)}, got {y.shape}"
            )
        result = np.asarray(self.rmatvec(y), dtype=np.complex128)
        if result.shape != (self.domain_dimension,):
            raise MatrixFreeError(
                f"rmatvec returned {result.shape}, expected {(self.domain_dimension,)}"
            )
        if not np.all(np.isfinite(result)):
            raise MatrixFreeError("adjoint action produced non-finite values")
        return result

    def materialize(self, *, max_elements: int = 4_000_000) -> Array:
        rows, columns = self.shape
        if rows * columns > max_elements:
            raise MatrixFreeError(
                f"materialization requires {rows * columns} elements, limit is {max_elements}"
            )
        matrix = np.empty((rows, columns), dtype=np.complex128)
        basis = np.zeros(columns, dtype=np.complex128)
        for index in range(columns):
            basis.fill(0.0)
            basis[index] = 1.0
            matrix[:, index] = self.apply(basis)
        return matrix

    def adjoint(self) -> "MatrixFreeOperator":
        if self.rmatvec is None:
            raise MatrixFreeError("cannot construct an adjoint without rmatvec")
        return MatrixFreeOperator(
            name=f"adjoint({self.name})",
            codomain_dimension=self.domain_dimension,
            domain_dimension=self.codomain_dimension,
            matvec=self.rmatvec,
            rmatvec=self.matvec,
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.codomain_id,
            codomain_id=self.domain_id,
            tags=tuple(sorted(set(self.tags + ("adjoint",)))),
        )

    def compose(self, inner: "MatrixFreeOperator", *, name: str | None = None) -> "MatrixFreeOperator":
        if self.domain_dimension != inner.codomain_dimension:
            raise TypeSystemError("matrix-free composition has incompatible dimensions")
        if self.domain_id is not None and inner.codomain_id is not None and self.domain_id != inner.codomain_id:
            raise TypeSystemError("matrix-free composition has incompatible named spaces")

        def action(x: Array) -> Array:
            return self.apply(inner.apply(x))

        adjoint_action: Matvec | None = None
        if self.rmatvec is not None and inner.rmatvec is not None:
            def adjoint_action(y: Array) -> Array:
                return inner.apply_adjoint(self.apply_adjoint(y))

        return MatrixFreeOperator(
            name=name or f"({self.name})@({inner.name})",
            codomain_dimension=self.codomain_dimension,
            domain_dimension=inner.domain_dimension,
            matvec=action,
            rmatvec=adjoint_action,
            scalar_system=self.math_type.compose_result(inner.math_type).scalar_system,
            units=self.units * inner.units,
            domain_id=inner.domain_id,
            codomain_id=self.codomain_id,
            tags=tuple(sorted(set(self.tags + inner.tags + ("composition",)))),
        )

    def add(self, other: "MatrixFreeOperator", *, name: str | None = None) -> "MatrixFreeOperator":
        self.math_type.require_same_additive_type(other.math_type)

        def action(x: Array) -> Array:
            return self.apply(x) + other.apply(x)

        adjoint_action: Matvec | None = None
        if self.rmatvec is not None and other.rmatvec is not None:
            def adjoint_action(y: Array) -> Array:
                return self.apply_adjoint(y) + other.apply_adjoint(y)

        return MatrixFreeOperator(
            name=name or f"({self.name})+({other.name})",
            codomain_dimension=self.codomain_dimension,
            domain_dimension=self.domain_dimension,
            matvec=action,
            rmatvec=adjoint_action,
            scalar_system=self.math_type.additive_result(other.math_type).scalar_system,
            units=self.units,
            domain_id=self.domain_id,
            codomain_id=self.codomain_id,
            tags=tuple(sorted(set(self.tags + other.tags + ("sum",)))),
        )

    def scale(self, scalar: complex, *, name: str | None = None) -> "MatrixFreeOperator":
        value = complex(scalar)

        def action(x: Array) -> Array:
            return value * self.apply(x)

        adjoint_action: Matvec | None = None
        if self.rmatvec is not None:
            def adjoint_action(y: Array) -> Array:
                return value.conjugate() * self.apply_adjoint(y)

        return MatrixFreeOperator(
            name=name or f"({value})*({self.name})",
            codomain_dimension=self.codomain_dimension,
            domain_dimension=self.domain_dimension,
            matvec=action,
            rmatvec=adjoint_action,
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.domain_id,
            codomain_id=self.codomain_id,
            tags=tuple(sorted(set(self.tags + ("scaled",)))),
        )

    def audit(self, *, trials: int = 16, seed: int = 0, tolerance: float = 1e-10) -> MatrixFreeAudit:
        if trials <= 0:
            raise MatrixFreeError("trials must be positive")
        rng = np.random.default_rng(seed)
        linearity = 0.0
        adjoint_residual: float | None = None
        norm_upper = 0.0
        finite = True
        adjoint_max = 0.0
        for _ in range(trials):
            x = rng.normal(size=self.domain_dimension) + 1j * rng.normal(size=self.domain_dimension)
            z = rng.normal(size=self.domain_dimension) + 1j * rng.normal(size=self.domain_dimension)
            a = complex(rng.normal(), rng.normal())
            b = complex(rng.normal(), rng.normal())
            lhs = self.apply(a * x + b * z)
            rhs = a * self.apply(x) + b * self.apply(z)
            denominator = max(float(np.linalg.norm(lhs)), float(np.linalg.norm(rhs)), np.finfo(float).eps)
            linearity = max(linearity, float(np.linalg.norm(lhs - rhs) / denominator))
            norm_upper = max(norm_upper, float(np.linalg.norm(self.apply(x)) / max(np.linalg.norm(x), np.finfo(float).eps)))
            finite = finite and bool(np.all(np.isfinite(lhs)))
            if self.rmatvec is not None:
                y = rng.normal(size=self.codomain_dimension) + 1j * rng.normal(size=self.codomain_dimension)
                left = np.vdot(self.apply(x), y)
                right = np.vdot(x, self.apply_adjoint(y))
                scale = max(abs(left), abs(right), np.finfo(float).eps)
                adjoint_max = max(adjoint_max, float(abs(left - right) / scale))
        if self.rmatvec is not None:
            adjoint_residual = adjoint_max
        passed = finite and linearity <= tolerance and (
            adjoint_residual is None or adjoint_residual <= tolerance
        )
        return MatrixFreeAudit(
            name=self.name,
            shape=self.shape,
            trials=trials,
            linearity_residual=linearity,
            adjoint_residual=adjoint_residual,
            norm_upper_estimate=norm_upper,
            finite=finite,
            passed=passed,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "shape": list(self.shape),
            "math_type": self.math_type.to_dict(),
            "has_rmatvec": self.rmatvec is not None,
            "tags": list(self.tags),
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
        }

    def digest(self) -> str:
        payload = json.dumps(self.metadata(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def from_dense(
        cls,
        matrix: npt.ArrayLike,
        *,
        name: str = "A",
        units: UnitDimension | None = None,
        domain_id: str | None = None,
        codomain_id: str | None = None,
    ) -> "MatrixFreeOperator":
        array = np.asarray(matrix, dtype=np.complex128)
        if array.ndim != 2 or not np.all(np.isfinite(array)):
            raise MatrixFreeError("dense source must be a finite matrix")
        frozen = array.copy()
        frozen.setflags(write=False)
        return cls(
            name=name,
            codomain_dimension=array.shape[0],
            domain_dimension=array.shape[1],
            matvec=lambda x: frozen @ x,
            rmatvec=lambda y: frozen.conj().T @ y,
            units=units or UnitDimension.dimensionless(),
            domain_id=domain_id,
            codomain_id=codomain_id,
            tags=("dense_reference",),
        )
