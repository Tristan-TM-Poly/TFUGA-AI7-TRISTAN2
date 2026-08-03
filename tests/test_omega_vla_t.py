import json

import numpy as np

from omega_vla_t import (
    LinearOperator,
    VectorSpace,
    audit_operator,
    basis_covariance_error,
    gradient,
    graph_divergence,
    graph_hodge_decomposition,
    graph_laplacian,
    laplacian,
)
from omega_vla_t.cli import benchmark_payload, main


def cycle_incidence() -> np.ndarray:
    return np.array(
        [
            [-1.0, 0.0, 1.0],
            [1.0, -1.0, 0.0],
            [0.0, 1.0, -1.0],
        ]
    )


def test_metric_duality_round_trip() -> None:
    metric = np.array([[2.0, 0.25], [0.25, 1.5]])
    space = VectorSpace(2, metric=metric)
    vector = np.array([1.5, -2.0])
    assert np.allclose(space.raise_index(space.covector(vector)), vector)
    assert space.norm(vector) > 0


def test_metric_adjoint_identity() -> None:
    domain = VectorSpace(2, metric=np.array([[2.0, 0.0], [0.0, 1.0]]))
    codomain = VectorSpace(2, metric=np.array([[1.0, 0.2], [0.2, 2.0]]))
    operator = LinearOperator(np.array([[1.0, 2.0], [-1.0, 0.5]]), domain, codomain)
    x = np.array([0.5, -1.0])
    y = np.array([2.0, 0.25])
    left = codomain.inner(operator.apply(x), y)
    adjoint_y = operator.adjoint_matrix() @ y
    right = domain.inner(x, adjoint_y)
    assert np.isclose(left, right)


def test_change_of_basis_covariance() -> None:
    space = VectorSpace(3)
    operator = LinearOperator(
        np.array([[2.0, 1.0, 0.0], [0.0, 3.0, -1.0], [1.0, 0.0, 2.0]]),
        space,
        space,
    )
    basis = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0], [1.0, 0.0, 1.0]])
    assert basis_covariance_error(operator, basis, np.array([1.0, -2.0, 0.5])) < 1e-12


def test_svd_rank_and_low_rank_approximation() -> None:
    space = VectorSpace(3)
    matrix = np.diag([5.0, 1.0, 1e-12])
    operator = LinearOperator(matrix, space, space)
    report = operator.svd_report(threshold=1e-10)
    approximation = operator.low_rank_approximation(2)
    assert report.exact_rank == 3
    assert report.threshold_rank == 2
    assert report.effective_rank > 1.0
    assert np.linalg.norm(matrix - approximation.matrix) < 1e-10


def test_grid_gradient_and_laplacian() -> None:
    axis = np.linspace(-1.0, 1.0, 21)
    dx = axis[1] - axis[0]
    x, y = np.meshgrid(axis, axis, indexing="ij")
    field = x**2 + y**2
    grad = gradient(field, spacing=(dx, dx))
    lap = laplacian(field, spacing=(dx, dx))
    assert grad.shape == (2, 21, 21)
    assert np.allclose(grad[:, 10, 10], 0.0, atol=1e-12)
    assert np.allclose(lap[2:-2, 2:-2], 4.0, atol=1e-10)


def test_graph_laplacian_and_hodge_invariants() -> None:
    incidence = cycle_incidence()
    lap = graph_laplacian(incidence)
    assert np.allclose(lap, lap.T)
    assert np.allclose(lap @ np.ones(3), 0.0)
    assert np.min(np.linalg.eigvalsh(lap)) > -1e-12

    flow = np.array([1.0, 2.0, 4.0])
    report = graph_hodge_decomposition(incidence, flow)
    assert report.reconstruction_error < 1e-12
    assert report.orthogonality_error < 1e-10
    assert np.linalg.norm(graph_divergence(incidence, report.cycle_flow)) < 1e-10


def test_oak_audit_is_explicitly_bounded() -> None:
    space = VectorSpace(2)
    operator = LinearOperator(np.array([[2.0, 0.5], [0.0, 1.0]]), space, space, name="StableFixture")
    report = audit_operator(operator, seed=11)
    assert report.passed
    assert report.status == "OAK_PASS_SOFTWARE_FIXTURE"
    assert report.scientific_validation_claimed is False
    assert report.theorem_claimed is False


def test_benchmark_is_deterministic_and_claim_safe() -> None:
    first = benchmark_payload(7)
    second = benchmark_payload(7)
    assert first == second
    assert first["claims"]["theorem_claimed"] is False
    assert first["claims"]["scientific_validation_claimed"] is False


def test_cli_writes_json(tmp_path) -> None:
    output = tmp_path / "benchmark.json"
    assert main(["benchmark", "--seed", "7", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["system"] == "Ω-VLA-T∞"
    assert payload["version"] == "R0.1"
