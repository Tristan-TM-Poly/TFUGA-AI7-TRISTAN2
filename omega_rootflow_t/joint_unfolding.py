"""Coupled local unfolding compiler for Ω-ROOTFLOW-T∞ R0.12.

A single coefficient perturbation acts on every multiple-root cluster at once.
R0.12 stacks the translation-normalized local unfolding jets of R0.8 across
all clusters from R0.10.

For cluster alpha with multiplicity m and

    alpha_m = P^(m)(c) / m!,

its local split-jet rows are

    J[alpha,q,j] = binom(k_j,q)c^(k_j-q)/alpha_m,
    q=0,...,m-2.

Since the mobile stratum matrix is

    A[alpha,q,j] = (k_j)_q c^(k_j-q),

we have row by row

    J = D A,

where D has nonzero diagonal entries 1/(q! alpha_m). Thus J and A have the
same first-order kernel. R0.12 checks that relation numerically rather than
merely assuming it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, factorial
from typing import Iterable

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value
from .multicluster import RootCluster, multi_cluster_tangent_space

ComplexArray = npt.NDArray[np.complex128]


def _encode(value: complex) -> list[float]:
    return [float(value.real), float(value.imag)]


def _vector(values: ComplexArray) -> list[list[float]]:
    return [_encode(complex(value)) for value in values]


def _matrix(values: ComplexArray) -> list[list[list[float]]]:
    return [_vector(row) for row in values]


@dataclass(frozen=True)
class JointUnfoldingBlock:
    cluster: RootCluster
    row_start: int
    row_stop: int
    leading_local_coefficient: complex

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster.to_dict(),
            "row_start": self.row_start,
            "row_stop": self.row_stop,
            "leading_local_coefficient": _encode(self.leading_local_coefficient),
        }


@dataclass(frozen=True)
class JointUnfoldingMap:
    clusters: tuple[RootCluster, ...]
    parameter_degrees: tuple[int, ...]
    blocks: tuple[JointUnfoldingBlock, ...]
    jet_matrix: ComplexArray
    jet_rank: int
    tangent_dimension: int
    mobile_constraint_rank: int
    row_scaling_residual: float
    kernel_rank_agreement: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "clusters": [item.to_dict() for item in self.clusters],
            "parameter_degrees": list(self.parameter_degrees),
            "blocks": [block.to_dict() for block in self.blocks],
            "jet_matrix": _matrix(self.jet_matrix),
            "jet_rank": self.jet_rank,
            "tangent_dimension": self.tangent_dimension,
            "mobile_constraint_rank": self.mobile_constraint_rank,
            "row_scaling_residual": self.row_scaling_residual,
            "kernel_rank_agreement": self.kernel_rank_agreement,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def joint_unfolding_map(
    coefficients: npt.ArrayLike,
    clusters: Iterable[RootCluster | tuple[complex, int]],
    parameter_degrees: npt.ArrayLike,
    *,
    rank_tolerance: float = 1e-10,
) -> JointUnfoldingMap:
    if rank_tolerance <= 0:
        raise ValueError("rank_tolerance must be positive")
    coeffs = _coefficients(coefficients)
    tangent = multi_cluster_tangent_space(coeffs, clusters, parameter_degrees)
    if tangent.status != "OAK_PASS_MULTICLUSTER_TANGENT_SPACE":
        raise ValueError(f"multicluster tangent model did not pass: {tangent.status}")

    rows: list[list[complex]] = []
    blocks: list[JointUnfoldingBlock] = []
    scaled_mobile_rows: list[ComplexArray] = []
    mobile_row_index = 0
    for cluster in tangent.clusters:
        leading = derivative_value(coeffs, cluster.root, order=cluster.multiplicity) / factorial(cluster.multiplicity)
        if abs(leading) <= rank_tolerance:
            raise ValueError("local leading coefficient is numerically zero")
        start = len(rows)
        for order in range(cluster.multiplicity - 1):
            row = [
                complex(comb(degree, order)) * cluster.root ** (degree - order) / leading
                if degree >= order
                else 0j
                for degree in tangent.parameter_degrees
            ]
            rows.append(row)
            scale = 1.0 / (factorial(order) * leading)
            scaled_mobile_rows.append(scale * tangent.constraint_matrix[mobile_row_index])
            mobile_row_index += 1
        blocks.append(JointUnfoldingBlock(cluster, start, len(rows), leading))
    jet = np.asarray(rows, dtype=np.complex128) if rows else np.empty((0, len(tangent.parameter_degrees)), dtype=np.complex128)
    scaled = np.asarray(scaled_mobile_rows, dtype=np.complex128) if scaled_mobile_rows else jet.copy()
    scaling_residual = float(np.max(np.abs(jet - scaled))) if jet.size else 0.0
    rank = int(np.linalg.matrix_rank(jet, tol=rank_tolerance))
    rank_agreement = rank == tangent.constraint_rank
    status = (
        "OAK_PASS_JOINT_UNFOLDING_MAP"
        if scaling_residual <= 1e-10 and rank_agreement
        else "OAK_WARN_JOINT_UNFOLDING_ALIGNMENT"
    )
    return JointUnfoldingMap(
        clusters=tangent.clusters,
        parameter_degrees=tangent.parameter_degrees,
        blocks=tuple(blocks),
        jet_matrix=jet,
        jet_rank=rank,
        tangent_dimension=len(tangent.parameter_degrees) - rank,
        mobile_constraint_rank=tangent.constraint_rank,
        row_scaling_residual=scaling_residual,
        kernel_rank_agreement=rank_agreement,
        status=status,
    )


@dataclass(frozen=True)
class ClusterSplitSignature:
    cluster: RootCluster
    local_jet: ComplexArray
    first_active_order: int | None
    predicted_puiseux_exponent: float | None
    local_factor_order: int | None
    splitting_branch_count: int
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster.to_dict(),
            "local_jet": _vector(self.local_jet),
            "first_active_order": self.first_active_order,
            "predicted_puiseux_exponent": self.predicted_puiseux_exponent,
            "local_factor_order": self.local_factor_order,
            "splitting_branch_count": self.splitting_branch_count,
            "status": self.status,
        }


@dataclass(frozen=True)
class JointDirectionAnalysis:
    direction: ComplexArray
    joint_jet: ComplexArray
    signatures: tuple[ClusterSplitSignature, ...]
    active_cluster_count: int
    first_order_stratum_tangent: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "direction": _vector(self.direction),
            "joint_jet": _vector(self.joint_jet),
            "signatures": [item.to_dict() for item in self.signatures],
            "active_cluster_count": self.active_cluster_count,
            "first_order_stratum_tangent": self.first_order_stratum_tangent,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def analyze_joint_direction(
    unfolding: JointUnfoldingMap,
    direction: npt.ArrayLike,
    *,
    activity_tolerance: float = 1e-10,
) -> JointDirectionAnalysis:
    if activity_tolerance <= 0:
        raise ValueError("activity_tolerance must be positive")
    vector = np.asarray(direction, dtype=np.complex128)
    if vector.ndim != 1 or vector.size != len(unfolding.parameter_degrees):
        raise ValueError("direction length must match parameter_degrees")
    jet = unfolding.jet_matrix @ vector
    signatures: list[ClusterSplitSignature] = []
    active_count = 0
    for block in unfolding.blocks:
        local = jet[block.row_start:block.row_stop]
        active = [index for index, value in enumerate(local) if abs(value) > activity_tolerance]
        if active:
            order = active[0]
            exponent = 1.0 / float(block.cluster.multiplicity - order)
            factor_order = order
            branch_count = block.cluster.multiplicity - order
            status = "OAK_PASS_CLUSTER_SPLIT_SIGNATURE"
            active_count += 1
        else:
            order = None
            exponent = None
            factor_order = None
            branch_count = 0
            status = "OAK_PASS_CLUSTER_FIRST_ORDER_PRESERVED"
        signatures.append(ClusterSplitSignature(block.cluster, local.copy(), order, exponent, factor_order, branch_count, status))
    tangent = active_count == 0
    status = "OAK_PASS_JOINT_TANGENT_DIRECTION" if tangent else "OAK_PASS_JOINT_SPLITTING_DIRECTION"
    return JointDirectionAnalysis(vector, jet, tuple(signatures), active_count, tangent, status)


@dataclass(frozen=True)
class JointUnfoldingDesign:
    target_jet: ComplexArray
    direction: ComplexArray
    predicted_jet: ComplexArray
    residual_norm: float
    direction_norm: float
    real_coefficients: bool
    realified_rank: int | None
    complex_rank: int
    analysis: JointDirectionAnalysis
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "target_jet": _vector(self.target_jet),
            "direction": _vector(self.direction),
            "predicted_jet": _vector(self.predicted_jet),
            "residual_norm": self.residual_norm,
            "direction_norm": self.direction_norm,
            "real_coefficients": self.real_coefficients,
            "realified_rank": self.realified_rank,
            "complex_rank": self.complex_rank,
            "analysis": self.analysis.to_dict(),
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def design_joint_unfolding(
    unfolding: JointUnfoldingMap,
    target_jet: npt.ArrayLike,
    *,
    real_coefficients: bool = False,
    tolerance: float = 1e-10,
) -> JointUnfoldingDesign:
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    target = np.asarray(target_jet, dtype=np.complex128)
    if target.ndim != 1 or target.size != unfolding.jet_matrix.shape[0]:
        raise ValueError("target_jet length must match joint unfolding row count")
    matrix = unfolding.jet_matrix
    complex_rank = int(np.linalg.matrix_rank(matrix, tol=tolerance))
    real_rank: int | None = None
    if real_coefficients:
        real_matrix = np.vstack((matrix.real, matrix.imag))
        real_target = np.concatenate((target.real, target.imag))
        direction_real, _, real_rank, _ = np.linalg.lstsq(real_matrix, real_target, rcond=tolerance)
        direction = direction_real.astype(np.complex128)
    else:
        direction, _, _, _ = np.linalg.lstsq(matrix, target, rcond=tolerance)
    predicted = matrix @ direction
    residual = float(np.linalg.norm(predicted - target))
    analysis = analyze_joint_direction(unfolding, direction, activity_tolerance=max(tolerance, 1e-10))
    status = "OAK_PASS_JOINT_UNFOLDING_DESIGN" if residual <= max(100.0 * tolerance, 1e-9) else "OAK_WARN_JOINT_UNFOLDING_TARGET_RESIDUAL"
    return JointUnfoldingDesign(
        target_jet=target,
        direction=np.asarray(direction, dtype=np.complex128),
        predicted_jet=predicted,
        residual_norm=residual,
        direction_norm=float(np.linalg.norm(direction)),
        real_coefficients=real_coefficients,
        realified_rank=real_rank,
        complex_rank=complex_rank,
        analysis=analysis,
        status=status,
    )
