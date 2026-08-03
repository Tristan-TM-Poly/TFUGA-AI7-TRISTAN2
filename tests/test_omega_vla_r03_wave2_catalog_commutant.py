from pathlib import Path

import numpy as np

from omega_vla_t.r03.operators import OperatorExpr, OperatorKind
from omega_vla_t.r03.types import MathType
from omega_vla_t.r03.wave2.commutant import (
    commutant_basis,
    simultaneous_commutant_basis,
)
from omega_vla_t.r03.wave2.egraph import EGraphBudget, saturate
from omega_vla_t.r03.wave2.families import (
    default_family_catalog,
    materialize_reference,
)
from omega_vla_t.r03.wave2.genome import OperatorGenome, OperatorGenomeRegistry
from omega_vla_t.r03.wave2.properties import infer_properties


def test_default_catalog_is_large_stable_and_searchable() -> None:
    catalog = default_family_catalog()
    assert len(catalog) >= 300
    assert len(catalog.digest()) == 64
    summary = catalog.summary()
    assert summary["families"] == len(catalog)
    assert summary["realms"]["physics"] >= 30
    assert summary["theorem_claimed"] is False
    hodge = catalog.search(text="Hodge")
    assert len(hodge) >= 3
    physics = catalog.search(realm="physics")
    assert all(value.realm == "physics" for value in physics)


def test_reference_materializers_are_deterministic() -> None:
    identifiers = (
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
    for family_id in identifiers:
        first = materialize_reference(family_id, 7, parameter=1.5)
        second = materialize_reference(family_id, 7, parameter=1.5)
        assert first.matrix.digest() == second.matrix.digest()
        assert first.math_type == second.math_type


def test_commutant_dimensions_and_residuals() -> None:
    diagonal = commutant_basis(np.diag([1.0, 2.0, 3.0]))
    scalar = commutant_basis(2.0 * np.eye(3))
    jordan = commutant_basis(np.array([[1.0, 1.0], [0.0, 1.0]]))
    assert diagonal.nullity == 3
    assert scalar.nullity == 9
    assert jordan.nullity == 2
    assert diagonal.maximum_commutator_residual < 1e-12
    assert scalar.identity_in_span_residual < 1e-12


def test_simultaneous_commutant_contains_identity() -> None:
    a = np.diag([1.0, 2.0, 3.0])
    b = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 3.0]])
    report = simultaneous_commutant_basis((a, b))
    assert report.nullity >= 1
    assert report.identity_in_span_residual < 1e-12
    assert report.maximum_commutator_residual < 1e-12
    assert report.theorem_claimed is False


def test_bounded_saturation_extracts_simplest_expression() -> None:
    operator_type = MathType.linear_operator(4, 4, domain_id="V", codomain_id="V")
    a = OperatorExpr.symbol("A", operator_type)
    identity = OperatorExpr.identity(operator_type)
    zero = OperatorExpr.zero(operator_type)
    expression = (
        (a.commutator(identity) + zero + (a @ identity))
        .adjoint()
        .adjoint()
    )
    report = saturate(
        expression,
        budget=EGraphBudget(
            max_rounds=8,
            max_expressions=2048,
            max_total_nodes=100_000,
            max_expression_nodes=512,
        ),
    )
    assert report.best_expression == a
    assert report.best_cost[0] == 1
    assert report.expressions_discovered >= 2
    assert report.formal_proof_claimed is False


def test_saturation_expands_commutator_under_budget() -> None:
    operator_type = MathType.linear_operator(2, 2, domain_id="V", codomain_id="V")
    a = OperatorExpr.symbol("A", operator_type)
    b = OperatorExpr.symbol("B", operator_type)
    report = saturate(
        a.commutator(b),
        budget=EGraphBudget(
            max_rounds=4,
            max_expressions=100,
            max_total_nodes=5000,
            max_expression_nodes=100,
        ),
    )
    assert report.expressions_discovered >= 2
    assert any(event.rule == "operator_classical_local" for event in report.events)


def test_genome_registry_deduplicates_and_persists(tmp_path: Path) -> None:
    operator = materialize_reference(
        "discrete_geometry.graphs_complexes.combinatorial_laplacian",
        6,
    )
    genome = OperatorGenome(
        genome_id="test.path_laplacian.n6",
        family_id="discrete_geometry.graphs_complexes.combinatorial_laplacian",
        name="Path Laplacian n=6",
        math_type=operator.math_type,
        representation="csr",
        parameters=(("dimension", "6"),),
        assumptions=("path graph", "unit weights"),
        invariants=("symmetric", "row structure"),
        algorithms=("CSR matvec",),
        backends=("python_reference",),
        property_evidence=infer_properties(operator.matrix.to_dense()),
        residuals=(("symmetry", 0.0),),
        provenance=("test fixture",),
        status="tested",
    )
    database = tmp_path / "genomes.sqlite3"
    export = tmp_path / "genomes.jsonl"
    with OperatorGenomeRegistry(database) as registry:
        inserted, digest = registry.add(genome)
        inserted_again, same_digest = registry.add(genome)
        assert inserted
        assert not inserted_again
        assert digest == same_digest
        assert registry.get(genome.genome_id) == genome
        assert registry.by_family(genome.family_id) == (genome,)
        assert registry.by_status("tested") == (genome,)
        assert registry.summary()["genomes"] == 1
        export_digest = registry.export_jsonl(export)
    assert len(export_digest) == 64
    assert export.read_text().count("\n") == 1


def test_operator_genome_rejects_unearned_theorem_claim() -> None:
    math_type = MathType.linear_operator(2, 2)
    try:
        OperatorGenome(
            genome_id="bad",
            family_id="foundations.elementary.identity",
            name="Bad claim",
            math_type=math_type,
            representation="symbolic",
            status="tested",
            theorem_claimed=True,
        )
    except ValueError as exc:
        assert "proof-level" in str(exc)
    else:
        raise AssertionError("unsupported theorem claim should be rejected")
