"""Deterministic benchmark multiverse for Ω-VLA Wave 2.

Default reports exclude wall-clock timing so they are byte-for-byte
reproducible. Optional timing measurements are clearly marked environmental.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from time import perf_counter_ns
from typing import Any, Iterable

import numpy as np

from .commutant import commutant_basis
from .families import default_family_catalog, materialize_reference
from .matrix_functions import matrix_exponential, matrix_logarithm, matrix_sign, matrix_square_root
from .properties import evidence_map, infer_properties


class BenchmarkError(ValueError):
    pass


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    family_id: str
    dimension: int
    parameter: float
    seed: int
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkResult:
    case: BenchmarkCase
    nnz: int
    density: float
    apply_residual: float
    adjoint_residual: float
    matrix_free_passed: bool
    detected_properties: tuple[str, ...]
    commutant_nullity: int | None
    environmental_runtime_ns: int | None = None
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FunctionBenchmarkResult:
    case_id: str
    function: str
    dimension: int
    residual: float
    passed: bool
    method: str
    iterations: int
    scaling_steps: int
    theorem_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkAtlasReport:
    catalog_families: int
    cases: tuple[BenchmarkResult, ...]
    matrix_functions: tuple[FunctionBenchmarkResult, ...]
    maximum_apply_residual: float
    maximum_adjoint_residual: float
    maximum_function_residual: float
    all_passed: bool
    deterministic_digest: str
    environmental_timing_included: bool
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_cases(
    *,
    dimensions: Iterable[int] = (4, 8, 16, 32),
    seed: int = 2026,
) -> tuple[BenchmarkCase, ...]:
    families = (
        "foundations.elementary.identity",
        "foundations.elementary.zero",
        "matrix_science.structured.diagonal",
        "matrix_science.structured.circulant",
        "matrix_science.structured.hilbert",
        "matrix_science.structured.permutation_matrix",
        "differential.continuous.first_derivative",
        "differential.continuous.second_derivative",
        "discrete_geometry.graphs_complexes.combinatorial_laplacian",
        "physics.equations.mass_matrix",
        "physics.equations.stiffness_matrix",
    )
    result = []
    for dimension in dimensions:
        if dimension <= 0:
            raise BenchmarkError("benchmark dimensions must be positive")
        for index, family_id in enumerate(families):
            result.append(
                BenchmarkCase(
                    case_id=f"{family_id}:n={dimension}",
                    family_id=family_id,
                    dimension=dimension,
                    parameter=1.0 + index / 10.0,
                    seed=seed + dimension * 100 + index,
                    tags=("deterministic", "reference_fixture"),
                )
            )
    return tuple(result)


def run_case(
    case: BenchmarkCase,
    *,
    tolerance: float = 1e-10,
    measure_timing: bool = False,
) -> BenchmarkResult:
    operator = materialize_reference(
        case.family_id,
        case.dimension,
        parameter=case.parameter,
    )
    dense = operator.matrix.to_dense()
    matrix_free = operator.to_matrix_free()
    rng = np.random.default_rng(case.seed)
    x = rng.normal(size=case.dimension) + 1j * rng.normal(size=case.dimension)
    y = rng.normal(size=case.dimension) + 1j * rng.normal(size=case.dimension)

    start = perf_counter_ns() if measure_timing else None
    sparse_result = operator.apply(x)
    runtime = perf_counter_ns() - start if start is not None else None
    dense_result = dense @ x
    apply_scale = max(float(np.linalg.norm(dense_result)), np.finfo(float).eps)
    apply_residual = float(np.linalg.norm(sparse_result - dense_result) / apply_scale)

    left = np.vdot(operator.apply(x), y)
    right = np.vdot(x, operator.adjoint().apply(y))
    adjoint_scale = max(abs(left), abs(right), np.finfo(float).eps)
    adjoint_residual = float(abs(left - right) / adjoint_scale)

    audit = matrix_free.audit(trials=8, seed=case.seed, tolerance=tolerance)
    properties = evidence_map(infer_properties(dense, tolerance=tolerance))
    detected = tuple(
        sorted(name for name, item in properties.items() if item.supported is True)
    )
    commutant_nullity: int | None = None
    if case.dimension <= 16:
        commutant_nullity = commutant_basis(dense, max_dimension=16).nullity

    return BenchmarkResult(
        case=case,
        nnz=operator.matrix.nnz,
        density=operator.matrix.density,
        apply_residual=apply_residual,
        adjoint_residual=adjoint_residual,
        matrix_free_passed=audit.passed,
        detected_properties=detected,
        commutant_nullity=commutant_nullity,
        environmental_runtime_ns=runtime,
    )


def _function_cases(tolerance: float) -> tuple[FunctionBenchmarkResult, ...]:
    matrices = {
        "diagonal_positive": np.diag([0.5, 1.0, 2.0]).astype(np.complex128),
        "rotation_generator": np.array([[0.0, -0.4], [0.4, 0.0]], dtype=np.complex128),
        "upper_triangular": np.array([[1.2, 0.1], [0.0, 2.0]], dtype=np.complex128),
    }
    results: list[FunctionBenchmarkResult] = []
    for case_id, matrix in matrices.items():
        exp_report = matrix_exponential(matrix, tolerance=tolerance)
        results.append(
            FunctionBenchmarkResult(
                case_id=case_id,
                function="exponential",
                dimension=matrix.shape[0],
                residual=exp_report.residual,
                passed=exp_report.passed,
                method=exp_report.method,
                iterations=exp_report.iterations,
                scaling_steps=exp_report.scaling_steps,
            )
        )

    positive = matrices["diagonal_positive"]
    for function_name, report in (
        ("square_root", matrix_square_root(positive, tolerance=tolerance)),
        ("logarithm", matrix_logarithm(positive, tolerance=tolerance)),
        ("sign", matrix_sign(np.diag([-2.0, 3.0]), tolerance=tolerance)),
    ):
        results.append(
            FunctionBenchmarkResult(
                case_id="diagonal_reference",
                function=function_name,
                dimension=report.shape[0],
                residual=report.residual,
                passed=report.passed,
                method=report.method,
                iterations=report.iterations,
                scaling_steps=report.scaling_steps,
            )
        )
    return tuple(results)


def run_atlas(
    *,
    dimensions: Iterable[int] = (4, 8, 16),
    seed: int = 2026,
    tolerance: float = 1e-10,
    measure_timing: bool = False,
) -> BenchmarkAtlasReport:
    cases = tuple(
        run_case(case, tolerance=tolerance, measure_timing=measure_timing)
        for case in default_cases(dimensions=dimensions, seed=seed)
    )
    functions = _function_cases(tolerance)
    maximum_apply = max((value.apply_residual for value in cases), default=0.0)
    maximum_adjoint = max((value.adjoint_residual for value in cases), default=0.0)
    finite_function_residuals = [
        value.residual for value in functions if np.isfinite(value.residual)
    ]
    maximum_function = max(finite_function_residuals, default=0.0)
    all_passed = (
        all(value.matrix_free_passed for value in cases)
        and maximum_apply <= tolerance
        and maximum_adjoint <= tolerance
        and all(value.passed for value in functions)
    )
    deterministic_payload = {
        "cases": [
            {
                **value.to_dict(),
                "environmental_runtime_ns": None,
            }
            for value in cases
        ],
        "matrix_functions": [value.to_dict() for value in functions],
    }
    digest = sha256(
        json.dumps(
            deterministic_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return BenchmarkAtlasReport(
        catalog_families=len(default_family_catalog()),
        cases=cases,
        matrix_functions=functions,
        maximum_apply_residual=maximum_apply,
        maximum_adjoint_residual=maximum_adjoint,
        maximum_function_residual=maximum_function,
        all_passed=all_passed,
        deterministic_digest=digest,
        environmental_timing_included=measure_timing,
    )


def logical_benchmark_frontier() -> dict[str, Any]:
    axes = {
        "families": len(default_family_catalog()),
        "dimensions": 64,
        "sparsity_regimes": 16,
        "condition_regimes": 16,
        "rank_regimes": 16,
        "noise_regimes": 8,
        "precisions": 8,
        "backends": 12,
        "hardware_classes": 8,
        "questions": 16,
    }
    size = 1
    for value in axes.values():
        size *= value
    return {
        "axes": axes,
        "logical_cases": size,
        "materialized_cases": 0,
        "permanent_total_cap": None,
        "claim_boundary": "logical benchmark addresses are not executed results",
    }
