"""Identity candidates, randomized fixtures and counterexample search.

The factory distinguishes algebraic schemas from proofs.  Numerical trials can
refute a universal claim or increase confidence in an implementation fixture;
they cannot prove the universal identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Callable, Iterable, Mapping

import numpy as np

from .evaluator import EvaluationLimits, evaluate_operator
from .operators import OperatorExpr, OperatorKind


class IdentityStatus(str, Enum):
    CANDIDATE = "candidate"
    NUMERICALLY_SUPPORTED = "numerically_supported"
    COUNTEREXAMPLE_FOUND = "counterexample_found"
    SYMBOLIC_SCHEMA = "symbolic_schema"
    FORMALIZED_INCOMPLETE = "formalized_incomplete"
    PROVED_EXTERNALLY = "proved_externally"


@dataclass(frozen=True)
class IdentityCandidate:
    identity_id: str
    title: str
    left: OperatorExpr
    right: OperatorExpr
    assumptions: tuple[str, ...]
    rationale: str
    falsifiers: tuple[str, ...]
    status: IdentityStatus = IdentityStatus.CANDIDATE
    theorem_claimed: bool = False

    def __post_init__(self) -> None:
        self.left.infer_type().require_same_additive_type(self.right.infer_type())
        if self.theorem_claimed and self.status != IdentityStatus.PROVED_EXTERNALLY:
            raise ValueError("theorem claims require externally verified proof evidence")

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "title": self.title,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "assumptions": list(self.assumptions),
            "rationale": self.rationale,
            "falsifiers": list(self.falsifiers),
            "status": self.status.value,
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Counterexample:
    identity_id: str
    trial: int
    environment: tuple[tuple[str, list[list[list[float]]]], ...]
    residual_norm: float
    relative_residual: float
    minimized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "trial": self.trial,
            "environment": dict(self.environment),
            "residual_norm": self.residual_norm,
            "relative_residual": self.relative_residual,
            "minimized": self.minimized,
            "theorem_claimed": False,
        }


@dataclass(frozen=True)
class IdentityTrialReport:
    identity_id: str
    trials: int
    passed_trials: int
    max_absolute_residual: float
    max_relative_residual: float
    counterexample: Counterexample | None
    status: IdentityStatus
    theorem_claimed: bool = False

    @property
    def passed(self) -> bool:
        return self.counterexample is None and self.passed_trials == self.trials

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "trials": self.trials,
            "passed_trials": self.passed_trials,
            "max_absolute_residual": self.max_absolute_residual,
            "max_relative_residual": self.max_relative_residual,
            "counterexample": None if self.counterexample is None else self.counterexample.to_dict(),
            "status": self.status.value,
            "passed": self.passed,
            "theorem_claimed": False,
            "formal_proof_claimed": False,
        }


class IdentityFactory:
    """Construct established algebraic schemas as non-proof software targets."""

    @staticmethod
    def adjoint_of_composition(a: OperatorExpr, b: OperatorExpr) -> IdentityCandidate:
        composed = a @ b
        left = composed.adjoint()
        right = b.adjoint() @ a.adjoint()
        return IdentityCandidate(
            identity_id="adjoint-compose",
            title="Adjoint reverses finite composition",
            left=left,
            right=right,
            assumptions=(
                "finite-dimensional inner-product spaces",
                "compatible domains and codomains",
                "adjoints taken with the declared metrics",
            ),
            rationale="Software schema for (AB)* = B*A*.",
            falsifiers=(
                "use incompatible spaces",
                "replace the metric adjoint by an unrelated transpose",
                "introduce a non-associative scalar algebra without explicit semantics",
            ),
            status=IdentityStatus.SYMBOLIC_SCHEMA,
        )

    @staticmethod
    def commutator_antisymmetry(a: OperatorExpr, b: OperatorExpr) -> IdentityCandidate:
        left = a.commutator(b)
        right = b.commutator(a).scale(-1)
        return IdentityCandidate(
            identity_id="commutator-antisymmetry",
            title="Commutator antisymmetry",
            left=left,
            right=right,
            assumptions=("finite compatible square operators",),
            rationale="Software schema for [A,B] = -[B,A].",
            falsifiers=("change subtraction order", "use incompatible operator shapes"),
            status=IdentityStatus.SYMBOLIC_SCHEMA,
        )

    @staticmethod
    def commutator_with_identity(a: OperatorExpr) -> IdentityCandidate:
        identity = OperatorExpr.identity(a.infer_type())
        left = a.commutator(identity)
        right = OperatorExpr.zero(a.infer_type())
        return IdentityCandidate(
            identity_id="commutator-identity-zero",
            title="Identity belongs to the center",
            left=left,
            right=right,
            assumptions=("finite square operator",),
            rationale="Software schema for [A,I] = 0.",
            falsifiers=("use an object that is not the identity on the same space",),
            status=IdentityStatus.SYMBOLIC_SCHEMA,
        )

    @staticmethod
    def tensor_adjoint(a: OperatorExpr, b: OperatorExpr) -> IdentityCandidate:
        left = a.tensor(b).adjoint()
        right = a.adjoint().tensor(b.adjoint())
        return IdentityCandidate(
            identity_id="tensor-adjoint",
            title="Adjoint distributes over finite tensor products",
            left=left,
            right=right,
            assumptions=("finite-dimensional Hilbert spaces", "standard tensor-product inner product"),
            rationale="Software schema for (A tensor B)* = A* tensor B*.",
            falsifiers=("change the tensor-product metric", "use unsupported non-associative scalars"),
            status=IdentityStatus.SYMBOLIC_SCHEMA,
        )

    @staticmethod
    def projection_idempotence(p: OperatorExpr) -> IdentityCandidate:
        left = p @ p
        right = p
        return IdentityCandidate(
            identity_id="projection-idempotence",
            title="Projection idempotence candidate",
            left=left,
            right=right,
            assumptions=("P is a projection",),
            rationale="This identity is conditional and is expected to fail for arbitrary matrices.",
            falsifiers=("sample a generic non-idempotent square matrix",),
            status=IdentityStatus.CANDIDATE,
        )


def run_identity_trials(
    candidate: IdentityCandidate,
    *,
    trials: int = 64,
    seed: int = 0,
    tolerance: float = 1e-10,
    environment_factory: Callable[[str, tuple[int, int], np.random.Generator], np.ndarray] | None = None,
) -> IdentityTrialReport:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    symbols = sorted(set(candidate.left.symbols()) | set(candidate.right.symbols()))
    symbol_types = _symbol_types(candidate.left)
    symbol_types.update(_symbol_types(candidate.right))
    generator = np.random.default_rng(seed)
    factory = environment_factory or _default_environment
    max_absolute = 0.0
    max_relative = 0.0

    for trial in range(trials):
        environment: dict[str, np.ndarray] = {}
        for symbol in symbols:
            shape = tuple(int(value) for value in symbol_types[symbol].shape.to_dict())
            environment[symbol] = factory(symbol, shape, generator)
        left = evaluate_operator(candidate.left, environment, simplify=False).matrix
        right = evaluate_operator(candidate.right, environment, simplify=False).matrix
        residual = left - right
        absolute = float(np.linalg.norm(residual))
        scale = max(float(np.linalg.norm(left)), float(np.linalg.norm(right)), np.finfo(float).eps)
        relative = absolute / scale
        max_absolute = max(max_absolute, absolute)
        max_relative = max(max_relative, relative)
        if relative > tolerance:
            encoded = tuple(
                (name, _encode_complex_matrix(value))
                for name, value in sorted(environment.items())
            )
            counterexample = Counterexample(
                identity_id=candidate.identity_id,
                trial=trial,
                environment=encoded,
                residual_norm=absolute,
                relative_residual=relative,
            )
            return IdentityTrialReport(
                identity_id=candidate.identity_id,
                trials=trials,
                passed_trials=trial,
                max_absolute_residual=max_absolute,
                max_relative_residual=max_relative,
                counterexample=counterexample,
                status=IdentityStatus.COUNTEREXAMPLE_FOUND,
            )
    return IdentityTrialReport(
        identity_id=candidate.identity_id,
        trials=trials,
        passed_trials=trials,
        max_absolute_residual=max_absolute,
        max_relative_residual=max_relative,
        counterexample=None,
        status=IdentityStatus.NUMERICALLY_SUPPORTED,
    )


def minimize_matrix_counterexample(
    candidate: IdentityCandidate,
    counterexample: Counterexample,
    *,
    tolerance: float = 1e-10,
) -> Counterexample:
    """Greedily zero entries while preserving a numerical violation."""

    environment = {
        name: _decode_complex_matrix(encoded)
        for name, encoded in counterexample.environment
    }
    changed = True
    while changed:
        changed = False
        for name in sorted(environment):
            matrix = environment[name]
            for index in np.ndindex(matrix.shape):
                original = matrix[index]
                if original == 0:
                    continue
                matrix[index] = 0
                if _identity_relative_residual(candidate, environment) > tolerance:
                    changed = True
                else:
                    matrix[index] = original
    residual = _identity_relative_residual(candidate, environment)
    absolute = float(
        np.linalg.norm(
            evaluate_operator(candidate.left, environment, simplify=False).matrix
            - evaluate_operator(candidate.right, environment, simplify=False).matrix
        )
    )
    return Counterexample(
        identity_id=counterexample.identity_id,
        trial=counterexample.trial,
        environment=tuple(
            (name, _encode_complex_matrix(value))
            for name, value in sorted(environment.items())
        ),
        residual_norm=absolute,
        relative_residual=residual,
        minimized=True,
    )


def _identity_relative_residual(
    candidate: IdentityCandidate,
    environment: Mapping[str, np.ndarray],
) -> float:
    left = evaluate_operator(candidate.left, environment, simplify=False).matrix
    right = evaluate_operator(candidate.right, environment, simplify=False).matrix
    absolute = float(np.linalg.norm(left - right))
    scale = max(float(np.linalg.norm(left)), float(np.linalg.norm(right)), np.finfo(float).eps)
    return absolute / scale


def _symbol_types(expression: OperatorExpr) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if expression.kind == OperatorKind.SYMBOL:
        result[expression.name] = expression.infer_type()
    for operand in expression.operands:
        for name, math_type in _symbol_types(operand).items():
            if name in result and result[name] != math_type:
                raise ValueError(f"symbol {name!r} has inconsistent types")
            result[name] = math_type
    return result


def _default_environment(
    symbol: str,
    shape: tuple[int, int],
    generator: np.random.Generator,
) -> np.ndarray:
    del symbol
    return generator.normal(size=shape) + 1j * generator.normal(size=shape)


def _encode_complex_matrix(matrix: np.ndarray) -> list[list[list[float]]]:
    return [
        [[float(value.real), float(value.imag)] for value in row]
        for row in np.asarray(matrix, dtype=np.complex128)
    ]


def _decode_complex_matrix(payload: list[list[list[float]]]) -> np.ndarray:
    return np.asarray(
        [[complex(real, imag) for real, imag in row] for row in payload],
        dtype=np.complex128,
    )
