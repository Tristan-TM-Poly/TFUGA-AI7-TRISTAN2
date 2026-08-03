import json

import numpy as np
import pytest

from omega_vla_t.r03 import (
    Backend,
    EvaluationLimits,
    IdentityFactory,
    IdentityStatus,
    MathType,
    OperatorError,
    OperatorExpr,
    OperatorKind,
    ScalarSystem,
    TypeSystemError,
    UnitDimension,
    audit_operator_expression,
    compile_latex,
    compile_lean4,
    compile_numpy,
    compile_rust_nalgebra,
    default_registry,
    evaluate_operator,
    finite_operator_fixture,
    minimize_matrix_counterexample,
    operator_expression_from_dict,
    run_identity_trials,
)


def square_type(size: int = 3) -> MathType:
    return MathType.linear_operator(
        size,
        size,
        scalar_system=ScalarSystem.COMPLEX,
        domain_id="V",
        codomain_id="V",
    )


def symbols(size: int = 3) -> tuple[OperatorExpr, OperatorExpr]:
    math_type = square_type(size)
    return OperatorExpr.symbol("A", math_type), OperatorExpr.symbol("B", math_type)


def random_environment(size: int = 3, seed: int = 0) -> dict[str, np.ndarray]:
    generator = np.random.default_rng(seed)
    return {
        "A": generator.normal(size=(size, size)) + 1j * generator.normal(size=(size, size)),
        "B": generator.normal(size=(size, size)) + 1j * generator.normal(size=(size, size)),
    }


def test_operator_grammar_infers_sum_composition_adjoint_and_tensor_types() -> None:
    a, b = symbols()
    assert (a + b).infer_type() == a.infer_type()
    assert (a @ b).infer_type() == a.infer_type()
    assert a.adjoint().infer_type() == a.infer_type()
    tensor_type = a.tensor(b).infer_type()
    assert tensor_type.shape.to_dict() == [9, 9]
    assert tensor_type.domain_id == "tensor(V,V)"
    assert tensor_type.codomain_id == "tensor(V,V)"


def test_operator_composition_rejects_incompatible_dimensions() -> None:
    outer = OperatorExpr.symbol(
        "A",
        MathType.linear_operator(4, 3, domain_id="V", codomain_id="W"),
    )
    inner = OperatorExpr.symbol(
        "B",
        MathType.linear_operator(2, 5, domain_id="U", codomain_id="X"),
    )
    with pytest.raises(TypeSystemError):
        (outer @ inner).infer_type()


def test_sum_rejects_unit_mismatch() -> None:
    left = OperatorExpr.symbol(
        "A",
        MathType.linear_operator(2, 2, units=UnitDimension.base("T").power(-1)),
    )
    right = OperatorExpr.symbol(
        "B",
        MathType.linear_operator(2, 2, units=UnitDimension.dimensionless()),
    )
    with pytest.raises(TypeSystemError):
        (left + right).infer_type()


def test_matrix_literal_validates_shape() -> None:
    matrix = OperatorExpr.matrix([[1, 2], [3, 4]], name="M")
    assert matrix.infer_type().shape.to_dict() == [2, 2]
    with pytest.raises(OperatorError):
        OperatorExpr.matrix([[1, 2], [3]])


def test_simplifier_removes_identity_zero_and_double_adjoint() -> None:
    a, b = symbols()
    identity = OperatorExpr.identity(a.infer_type())
    zero = OperatorExpr.zero(a.infer_type())
    assert (a @ identity).simplify() == a
    assert (identity @ a).simplify() == a
    assert (a + zero).simplify() == a
    assert (a - a).simplify().kind == OperatorKind.ZERO
    assert a.adjoint().adjoint().simplify() == a
    assert a.commutator(a).simplify().kind == OperatorKind.ZERO
    assert a.commutator(identity).simplify().kind == OperatorKind.ZERO
    assert (a @ b).adjoint().simplify() == (b.adjoint() @ a.adjoint()).simplify()


def test_simplifier_is_idempotent_and_reduces_fixture() -> None:
    expression, _ = finite_operator_fixture()
    simplified = expression.simplify()
    assert simplified.simplify() == simplified
    assert simplified.node_count() <= expression.node_count()
    assert simplified.kind == OperatorKind.ZERO


def test_operator_serialization_round_trip_and_digest() -> None:
    a, b = symbols(2)
    expression = (a.adjoint() @ b + b.adjoint() @ a).scale(0.5)
    reconstructed = operator_expression_from_dict(expression.to_dict())
    assert reconstructed == expression
    assert reconstructed.digest() == expression.digest()
    assert reconstructed.canonical_json() == expression.canonical_json()


def test_evaluator_matches_direct_numpy_computation() -> None:
    a, b = symbols(3)
    expression = a.commutator(b) + a.adjoint()
    environment = random_environment(3, seed=11)
    report = evaluate_operator(expression, environment, simplify=False)
    expected = (
        environment["A"] @ environment["B"]
        - environment["B"] @ environment["A"]
        + environment["A"].conj().T
    )
    assert np.allclose(report.matrix, expected)
    assert report.finite
    assert report.node_count_after == report.node_count_before
    assert report.theorem_claimed is False


def test_evaluator_handles_matrix_inverse_power_tensor_and_direct_sum() -> None:
    matrix = OperatorExpr.matrix([[2.0, 0.0], [0.0, 4.0]])
    inverse = OperatorExpr.unary(OperatorKind.INVERSE, matrix)
    power = OperatorExpr.unary(OperatorKind.POWER, matrix, exponent=3)
    tensor = matrix.tensor(matrix)
    direct = OperatorExpr.nary(OperatorKind.DIRECT_SUM, (matrix, matrix))
    assert np.allclose(evaluate_operator(inverse).matrix, np.diag([0.5, 0.25]))
    assert np.allclose(evaluate_operator(power).matrix, np.diag([8.0, 64.0]))
    assert evaluate_operator(tensor).matrix.shape == (4, 4)
    assert evaluate_operator(direct).matrix.shape == (4, 4)


def test_evaluator_enforces_resource_limits_and_bindings() -> None:
    a, _ = symbols(2)
    with pytest.raises(OperatorError):
        evaluate_operator(a, {})
    with pytest.raises(OperatorError):
        evaluate_operator(
            a.tensor(a),
            {"A": np.eye(2)},
            limits=EvaluationLimits(max_matrix_elements=8),
        )


def test_exponential_reference_backend_handles_diagonal_fixture() -> None:
    matrix = OperatorExpr.matrix([[0.0, 0.0], [0.0, 1.0]])
    expression = OperatorExpr.unary(OperatorKind.EXPONENTIAL, matrix)
    result = evaluate_operator(expression).matrix
    assert np.allclose(result, np.diag([1.0, np.e]))


def test_latex_compiler_covers_operator_grammar() -> None:
    a, b = symbols(2)
    expression = a.adjoint().commutator(b).tensor(a + b)
    artifact = compile_latex(expression)
    assert artifact.complete
    assert "\\left[" in artifact.content
    assert "\\otimes" in artifact.content
    assert artifact.theorem_claimed is False


def test_numpy_compiler_emits_deterministic_executable_source() -> None:
    a, b = symbols(2)
    expression = a.commutator(b) + a.adjoint()
    first = compile_numpy(expression)
    second = compile_numpy(expression)
    assert first.content == second.content
    assert first.complete
    namespace: dict[str, object] = {}
    exec(first.content, namespace)
    environment = random_environment(2, seed=17)
    generated = namespace["evaluate"](environment)
    reference = evaluate_operator(expression, environment, simplify=False).matrix
    assert np.allclose(generated, reference)
    assert namespace["THEOREM_CLAIMED"] is False


def test_rust_compiler_emits_bounded_source_without_claims() -> None:
    a, b = symbols(2)
    artifact = compile_rust_nalgebra(a.commutator(b))
    assert artifact.complete
    assert "nalgebra" in artifact.content
    assert "THEOREM_CLAIMED: bool = false" in artifact.content
    assert artifact.formal_proof_claimed is False


def test_lean_compiler_is_explicitly_incomplete() -> None:
    a, _ = symbols(2)
    artifact = compile_lean4(a.adjoint())
    assert artifact.complete is False
    assert artifact.executable is False
    assert "FORMALIZED_INCOMPLETE" in artifact.content
    assert "formallyVerified : Bool := false" in artifact.content
    assert "theorem generated_target : True" in artifact.content
    assert artifact.formal_proof_claimed is False


def test_compiler_registry_lists_stable_backends() -> None:
    assert default_registry().backends() == (
        "json",
        "latex",
        "lean4",
        "numpy",
        "rust-nalgebra",
    )


def test_established_identity_schemas_pass_numerical_trials() -> None:
    a, b = symbols(3)
    candidates = (
        IdentityFactory.adjoint_of_composition(a, b),
        IdentityFactory.commutator_antisymmetry(a, b),
        IdentityFactory.commutator_with_identity(a),
        IdentityFactory.tensor_adjoint(a, b),
    )
    for index, candidate in enumerate(candidates):
        report = run_identity_trials(candidate, trials=12, seed=100 + index)
        assert report.passed
        assert report.status == IdentityStatus.NUMERICALLY_SUPPORTED
        assert report.counterexample is None
        assert report.theorem_claimed is False


def test_projection_identity_finds_and_minimizes_counterexample() -> None:
    p = OperatorExpr.symbol("P", square_type(2))
    candidate = IdentityFactory.projection_idempotence(p)
    report = run_identity_trials(candidate, trials=4, seed=99)
    assert not report.passed
    assert report.status == IdentityStatus.COUNTEREXAMPLE_FOUND
    assert report.counterexample is not None
    minimized = minimize_matrix_counterexample(candidate, report.counterexample)
    assert minimized.minimized
    assert minimized.relative_residual > 1e-10


def test_oak_operator_report_passes_bound_fixture_and_preserves_claim_boundaries() -> None:
    expression, environment = finite_operator_fixture()
    report = audit_operator_expression(expression, environment)
    assert report.passed
    payload = report.to_dict()
    assert payload["status"] == "OAK_PASS_OPERATOR_FIXTURE_R0_3"
    assert payload["theorem_claimed"] is False
    assert payload["formal_proof_claimed"] is False
    assert payload["scientific_validation_claimed"] is False
    assert len(payload["gates"]) == 12


def test_oak_operator_report_fails_invalid_composition() -> None:
    outer = OperatorExpr.symbol("A", MathType.linear_operator(3, 2))
    inner = OperatorExpr.symbol("B", MathType.linear_operator(4, 5))
    report = audit_operator_expression(outer @ inner)
    assert not report.passed
    assert report.status == "OAK_FAIL_OPERATOR_FIXTURE_R0_3"
    assert any(gate.name == "typing" and not gate.passed for gate in report.gates)
