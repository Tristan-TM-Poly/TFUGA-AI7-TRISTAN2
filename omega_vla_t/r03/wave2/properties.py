"""Evidence-aware numerical property inference for finite operators.

Properties are never returned as bare booleans. Every conclusion carries a
residual, threshold, method and evidence level so numerical observation cannot
silently become proof.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.complex128]


class PropertyInferenceError(ValueError):
    pass


class EvidenceLevel(str, Enum):
    UNKNOWN = "unknown"
    DECLARED = "declared"
    NUMERICALLY_TESTED = "numerically_tested"
    NUMERICALLY_REFUTED = "numerically_refuted"
    SYMBOLICALLY_DERIVED = "symbolically_derived"
    FORMALLY_VERIFIED = "formally_verified"


@dataclass(frozen=True)
class PropertyEvidence:
    property_name: str
    supported: bool | None
    evidence_level: EvidenceLevel
    residual: float | None
    threshold: float | None
    method: str
    assumptions: tuple[str, ...] = ()
    witnesses: tuple[str, ...] = ()
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _matrix(value: npt.ArrayLike) -> Array:
    matrix = np.asarray(value, dtype=np.complex128)
    if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
        raise PropertyInferenceError("property inference requires a finite matrix")
    return matrix


def _relative(numerator: Array, reference: Array) -> float:
    scale = max(float(np.linalg.norm(reference, ord="fro")), np.finfo(float).eps)
    return float(np.linalg.norm(numerator, ord="fro") / scale)


def _evidence(
    name: str,
    residual: float,
    threshold: float,
    method: str,
    *,
    assumptions: Iterable[str] = (),
    witnesses: Iterable[str] = (),
) -> PropertyEvidence:
    supported = residual <= threshold
    return PropertyEvidence(
        property_name=name,
        supported=supported,
        evidence_level=(
            EvidenceLevel.NUMERICALLY_TESTED
            if supported
            else EvidenceLevel.NUMERICALLY_REFUTED
        ),
        residual=residual,
        threshold=threshold,
        method=method,
        assumptions=tuple(assumptions),
        witnesses=tuple(witnesses),
    )


def infer_properties(
    value: npt.ArrayLike,
    *,
    tolerance: float = 1e-10,
) -> tuple[PropertyEvidence, ...]:
    """Infer a conservative property atlas for one finite matrix."""

    a = _matrix(value)
    rows, columns = a.shape
    results: list[PropertyEvidence] = []
    zero_reference = np.zeros_like(a)
    results.append(_evidence("zero", _relative(a, np.eye(rows, columns)), tolerance, "frobenius_norm"))

    if rows != columns:
        results.extend(
            PropertyEvidence(
                property_name=name,
                supported=None,
                evidence_level=EvidenceLevel.UNKNOWN,
                residual=None,
                threshold=tolerance,
                method="requires_square_matrix",
            )
            for name in (
                "identity",
                "self_adjoint",
                "skew_adjoint",
                "normal",
                "unitary",
                "projection",
                "involution",
                "positive_semidefinite",
                "positive_definite",
            )
        )
        return tuple(results)

    identity = np.eye(rows, dtype=np.complex128)
    adjoint = a.conj().T
    results.append(_evidence("identity", _relative(a - identity, identity), tolerance, "A-I"))
    results.append(_evidence("self_adjoint", _relative(a - adjoint, a), tolerance, "A-A*"))
    results.append(_evidence("skew_adjoint", _relative(a + adjoint, a), tolerance, "A+A*"))
    results.append(_evidence("normal", _relative(a @ adjoint - adjoint @ a, a), tolerance, "AA*-A*A"))
    results.append(_evidence("unitary", _relative(adjoint @ a - identity, identity), tolerance, "A*A-I"))
    results.append(_evidence("projection", _relative(a @ a - a, a), tolerance, "A^2-A"))
    results.append(_evidence("involution", _relative(a @ a - identity, identity), tolerance, "A^2-I"))

    singular_values = np.linalg.svd(a, compute_uv=False)
    rank_tolerance = max(a.shape) * np.finfo(float).eps * (
        float(singular_values[0]) if singular_values.size else 0.0
    )
    numerical_rank = int(np.sum(singular_values > rank_tolerance))
    determinant = complex(np.linalg.det(a))
    condition = float(np.linalg.cond(a))
    invertible_residual = 0.0 if numerical_rank == rows else 1.0
    results.append(
        _evidence(
            "invertible",
            invertible_residual,
            0.5,
            "svd_rank",
            witnesses=(
                f"numerical_rank={numerical_rank}",
                f"determinant={determinant}",
                f"condition={condition}",
            ),
        )
    )

    hermitian_part = 0.5 * (a + adjoint)
    antihermitian_residual = _relative(a - adjoint, a)
    if antihermitian_residual <= tolerance:
        eigenvalues = np.linalg.eigvalsh(hermitian_part)
        minimum = float(np.min(eigenvalues, initial=0.0))
        psd_residual = max(0.0, -minimum)
        pd_residual = max(0.0, tolerance - minimum)
        results.append(
            _evidence(
                "positive_semidefinite",
                psd_residual,
                tolerance,
                "eigvalsh",
                assumptions=("self_adjoint within threshold",),
                witnesses=(f"minimum_eigenvalue={minimum}",),
            )
        )
        results.append(
            _evidence(
                "positive_definite",
                pd_residual,
                tolerance,
                "eigvalsh",
                assumptions=("self_adjoint within threshold",),
                witnesses=(f"minimum_eigenvalue={minimum}",),
            )
        )
    else:
        for name in ("positive_semidefinite", "positive_definite"):
            results.append(
                PropertyEvidence(
                    property_name=name,
                    supported=None,
                    evidence_level=EvidenceLevel.UNKNOWN,
                    residual=None,
                    threshold=tolerance,
                    method="requires_self_adjoint_matrix",
                    assumptions=("self_adjoint",),
                )
            )

    trace = complex(np.trace(a))
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(a)), initial=0.0))
    results.extend(
        (
            PropertyEvidence(
                property_name="numerical_rank",
                supported=None,
                evidence_level=EvidenceLevel.NUMERICALLY_TESTED,
                residual=None,
                threshold=rank_tolerance,
                method="svd",
                witnesses=(f"value={numerical_rank}",),
            ),
            PropertyEvidence(
                property_name="trace",
                supported=None,
                evidence_level=EvidenceLevel.NUMERICALLY_TESTED,
                residual=None,
                threshold=None,
                method="diagonal_sum",
                witnesses=(f"value={trace}",),
            ),
            PropertyEvidence(
                property_name="spectral_radius",
                supported=None,
                evidence_level=EvidenceLevel.NUMERICALLY_TESTED,
                residual=None,
                threshold=None,
                method="dense_eigvals",
                witnesses=(f"value={spectral_radius}",),
            ),
        )
    )
    return tuple(sorted(results, key=lambda item: item.property_name))


def evidence_map(evidence: Iterable[PropertyEvidence]) -> dict[str, PropertyEvidence]:
    result: dict[str, PropertyEvidence] = {}
    for item in evidence:
        if item.property_name in result:
            raise PropertyInferenceError(f"duplicate property evidence: {item.property_name}")
        result[item.property_name] = item
    return result
