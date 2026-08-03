"""OAK audit for Ω-VLA R0.3 Wave 2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from ..operators import OperatorExpr, OperatorKind
from ..types import MathType
from .benchmarks import logical_benchmark_frontier, run_atlas
from .commutant import commutant_basis, simultaneous_commutant_basis
from .egraph import EGraphBudget, saturate
from .families import default_family_catalog, materialize_reference
from .genome import OperatorGenome, OperatorGenomeRegistry
from .matrix_free import MatrixFreeOperator
from .matrix_functions import matrix_exponential, matrix_logarithm, matrix_sign, matrix_square_root
from .properties import evidence_map, infer_properties
from .sparse import CSRMatrix


@dataclass(frozen=True)
class OAKCheck:
    name: str
    passed: bool
    metric: float | int | str | None
    threshold: float | int | str | None
    detail: str


@dataclass(frozen=True)
class Wave2OAKReport:
    version: str
    passed: bool
    status: str
    checks: tuple[OAKCheck, ...]
    family_count: int
    logical_benchmark_cases: int
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_wave2(*, tolerance: float = 1e-9) -> Wave2OAKReport:
    checks: list[OAKCheck] = []
    catalog = default_family_catalog()
    checks.append(
        OAKCheck(
            "operator_family_catalog",
            len(catalog) >= 250,
            len(catalog),
            ">=250",
            "stable metadata families, not theorem counts",
        )
    )
    checks.append(
        OAKCheck(
            "catalog_digest",
            len(catalog.digest()) == 64,
            len(catalog.digest()),
            64,
            catalog.digest(),
        )
    )

    laplacian = CSRMatrix.laplacian_1d(8)
    dense = laplacian.to_dense()
    x = np.arange(8, dtype=np.complex128)
    sparse_residual = float(np.linalg.norm(laplacian.matvec(x) - dense @ x))
    checks.append(
        OAKCheck(
            "csr_dense_equivalence",
            sparse_residual <= tolerance,
            sparse_residual,
            tolerance,
            "CSR matvec compared with dense reference",
        )
    )
    product = laplacian.matmul(CSRMatrix.identity(8)).to_dense()
    product_residual = float(np.linalg.norm(product - dense))
    checks.append(
        OAKCheck(
            "csr_identity_product",
            product_residual <= tolerance,
            product_residual,
            tolerance,
            "sparse multiplication by identity",
        )
    )

    matrix_free = MatrixFreeOperator.from_dense(dense, name="L")
    mf_audit = matrix_free.audit(trials=12, seed=2026, tolerance=tolerance)
    checks.append(
        OAKCheck(
            "matrix_free_linearity_adjoint",
            mf_audit.passed,
            max(mf_audit.linearity_residual, mf_audit.adjoint_residual or 0.0),
            tolerance,
            "randomized finite fixture",
        )
    )

    positive = np.diag([0.5, 1.0, 2.0]).astype(np.complex128)
    function_reports = (
        matrix_exponential(np.array([[0.0, -0.2], [0.2, 0.0]]), tolerance=tolerance),
        matrix_square_root(positive, tolerance=tolerance),
        matrix_logarithm(positive, tolerance=tolerance),
        matrix_sign(np.diag([-2.0, 3.0]), tolerance=tolerance),
    )
    maximum_function_residual = max(
        value.residual for value in function_reports if np.isfinite(value.residual)
    )
    checks.append(
        OAKCheck(
            "matrix_function_residuals",
            all(value.passed for value in function_reports),
            maximum_function_residual,
            tolerance * 1000,
            ", ".join(value.method for value in function_reports),
        )
    )

    properties = evidence_map(infer_properties(positive, tolerance=tolerance))
    property_passed = (
        properties["self_adjoint"].supported is True
        and properties["positive_definite"].supported is True
        and properties["unitary"].supported is False
    )
    checks.append(
        OAKCheck(
            "evidence_aware_properties",
            property_passed,
            str({key: properties[key].supported for key in ("self_adjoint", "positive_definite", "unitary")}),
            "expected evidence map",
            "numerical evidence remains non-proof",
        )
    )

    diagonal_commutant = commutant_basis(np.diag([1.0, 2.0, 3.0]))
    scalar_commutant = commutant_basis(2.0 * np.eye(3))
    simultaneous = simultaneous_commutant_basis(
        (np.diag([1.0, 2.0]), np.array([[0.0, 1.0], [1.0, 0.0]]))
    )
    commutant_passed = (
        diagonal_commutant.nullity == 3
        and scalar_commutant.nullity == 9
        and simultaneous.identity_in_span_residual <= tolerance
        and diagonal_commutant.maximum_commutator_residual <= tolerance
    )
    checks.append(
        OAKCheck(
            "commutant_solver",
            commutant_passed,
            f"diag={diagonal_commutant.nullity},scalar={scalar_commutant.nullity},sim={simultaneous.nullity}",
            "3,9,identity in span",
            "dense SVD finite centralizer fixtures",
        )
    )

    operator_type = MathType.linear_operator(3, 3, domain_id="V", codomain_id="V")
    a = OperatorExpr.symbol("A", operator_type)
    identity = OperatorExpr.identity(operator_type)
    expression = (a.commutator(identity) + (a @ identity)).adjoint().adjoint()
    saturation = saturate(
        expression,
        budget=EGraphBudget(
            max_rounds=8,
            max_expressions=1024,
            max_total_nodes=50_000,
            max_expression_nodes=256,
        ),
    )
    checks.append(
        OAKCheck(
            "rewrite_saturation",
            saturation.best_expression.simplify() == a,
            saturation.expressions_discovered,
            "bounded and best=A",
            saturation.stopped_reason,
        )
    )

    reference = materialize_reference(
        "discrete_geometry.graphs_complexes.combinatorial_laplacian",
        6,
    )
    evidence = infer_properties(reference.matrix.to_dense(), tolerance=tolerance)
    genome = OperatorGenome(
        genome_id="oak.wave2.path_laplacian.n6",
        family_id="discrete_geometry.graphs_complexes.combinatorial_laplacian",
        name="Path Laplacian n=6",
        math_type=reference.math_type,
        representation="csr",
        parameters=(("dimension", "6"),),
        assumptions=("path graph", "unit weights"),
        invariants=("row sum zero",),
        algorithms=("CSR matvec",),
        backends=("python_reference",),
        property_evidence=evidence,
        residuals=(("symmetry", float(np.linalg.norm(reference.matrix.to_dense() - reference.matrix.to_dense().T))),),
        provenance=("generated by OAK Wave 2 fixture",),
        status="tested",
    )
    with OperatorGenomeRegistry() as registry:
        inserted, digest = registry.add(genome)
        duplicate_inserted, duplicate_digest = registry.add(genome)
        loaded = registry.get(genome.genome_id)
        registry_passed = (
            inserted
            and not duplicate_inserted
            and digest == duplicate_digest == loaded.digest()
            and registry.count() == 1
        )
    checks.append(
        OAKCheck(
            "operator_genome_registry",
            registry_passed,
            digest,
            loaded.digest(),
            "content-addressed SQLite deduplication",
        )
    )

    atlas = run_atlas(dimensions=(4, 8), seed=2026, tolerance=tolerance)
    checks.append(
        OAKCheck(
            "benchmark_atlas",
            atlas.all_passed,
            len(atlas.cases),
            ">=20 deterministic cases",
            atlas.deterministic_digest,
        )
    )

    frontier = logical_benchmark_frontier()
    logical_cases = int(frontier["logical_cases"])
    checks.append(
        OAKCheck(
            "logical_benchmark_frontier",
            logical_cases > 10**12 and frontier["permanent_total_cap"] is None,
            logical_cases,
            ">1e12 and no permanent cap",
            "logical addresses are not executed results",
        )
    )

    passed = all(check.passed for check in checks)
    return Wave2OAKReport(
        version="R0.3-OMEGA-WAVE-2-MAX",
        passed=passed,
        status=(
            "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_2"
            if passed
            else "OAK_FAIL_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_2"
        ),
        checks=tuple(checks),
        family_count=len(catalog),
        logical_benchmark_cases=logical_cases,
    )
