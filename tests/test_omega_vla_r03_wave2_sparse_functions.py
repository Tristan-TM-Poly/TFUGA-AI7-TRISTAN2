import numpy as np

from omega_vla_t.r03.wave2.matrix_free import MatrixFreeOperator
from omega_vla_t.r03.wave2.matrix_functions import (
    MatrixFunctionError,
    matrix_exponential,
    matrix_logarithm,
    matrix_sign,
    matrix_square_root,
)
from omega_vla_t.r03.wave2.properties import evidence_map, infer_properties
from omega_vla_t.r03.wave2.sparse import CSRMatrix, SparseError, SparseOperator


def test_csr_round_trip_matvec_adjoint_add_and_multiply() -> None:
    dense = np.array(
        [
            [2.0, 0.0, -1.0],
            [0.0, 3.0, 0.0],
            [4.0, 0.0, 5.0],
        ],
        dtype=np.complex128,
    )
    csr = CSRMatrix.from_dense(dense)
    assert csr.nnz == 5
    assert np.allclose(csr.to_dense(), dense)
    vector = np.array([1.0, 2.0, -1.0])
    assert np.allclose(csr.matvec(vector), dense @ vector)
    assert np.allclose(csr.adjoint().to_dense(), dense.conj().T)
    assert np.allclose(csr.add(csr).to_dense(), 2.0 * dense)
    assert np.allclose(csr.matmul(CSRMatrix.identity(3)).to_dense(), dense)


def test_csr_coo_canonicalizes_duplicates_and_kronecker() -> None:
    csr = CSRMatrix.from_coo(
        2,
        2,
        [(0, 0, 1.0), (0, 0, 2.0), (1, 1, 4.0)],
    )
    assert csr.data == (3.0 + 0.0j, 4.0 + 0.0j)
    kron = csr.kronecker(CSRMatrix.identity(2)).to_dense()
    assert np.allclose(kron, np.kron(csr.to_dense(), np.eye(2)))


def test_laplacian_boundaries_and_sparse_operator_adjoint() -> None:
    for boundary in ("dirichlet", "neumann", "periodic"):
        matrix = CSRMatrix.laplacian_1d(8, boundary=boundary)
        assert matrix.shape == (8, 8)
        assert np.allclose(matrix.to_dense(), matrix.to_dense().T)
    operator = SparseOperator("L", CSRMatrix.laplacian_1d(6))
    vector = np.arange(6, dtype=float)
    assert np.allclose(operator.apply(vector), operator.adjoint().apply(vector))


def test_matrix_free_dense_composition_sum_scale_and_audit() -> None:
    a = np.array([[2.0, 1.0], [0.0, 3.0]], dtype=np.complex128)
    b = np.array([[1.0, 0.0], [4.0, 1.0]], dtype=np.complex128)
    op_a = MatrixFreeOperator.from_dense(a, name="A", domain_id="V", codomain_id="V")
    op_b = MatrixFreeOperator.from_dense(b, name="B", domain_id="V", codomain_id="V")
    x = np.array([1.0, -2.0], dtype=np.complex128)
    assert np.allclose(op_a.compose(op_b).apply(x), a @ b @ x)
    assert np.allclose(op_a.add(op_b).apply(x), (a + b) @ x)
    assert np.allclose(op_a.scale(2.0j).apply(x), 2.0j * a @ x)
    assert np.allclose(op_a.materialize(), a)
    audit = op_a.audit(trials=32, seed=9)
    assert audit.passed
    assert audit.linearity_residual < 1e-12
    assert audit.adjoint_residual is not None
    assert audit.adjoint_residual < 1e-12


def test_matrix_exponential_rotation_and_inverse_identity() -> None:
    generator = np.array([[0.0, -0.4], [0.4, 0.0]], dtype=np.complex128)
    report = matrix_exponential(generator)
    expected = np.array(
        [[np.cos(0.4), -np.sin(0.4)], [np.sin(0.4), np.cos(0.4)]],
        dtype=np.complex128,
    )
    assert report.passed
    assert report.residual < 1e-10
    assert np.allclose(report.result, expected, atol=1e-11)


def test_matrix_logarithm_square_root_and_sign() -> None:
    positive = np.diag([0.5, 1.0, 2.0]).astype(np.complex128)
    root = matrix_square_root(positive)
    logarithm = matrix_logarithm(positive)
    sign = matrix_sign(np.diag([-2.0, 3.0]))
    assert root.passed and logarithm.passed and sign.passed
    assert np.allclose(root.result @ root.result, positive, atol=1e-10)
    assert np.allclose(logarithm.result, np.diag(np.log([0.5, 1.0, 2.0])), atol=1e-9)
    assert np.allclose(sign.result, np.diag([-1.0, 1.0]), atol=1e-10)


def test_matrix_logarithm_rejects_invalid_principal_branch() -> None:
    for matrix in (np.diag([0.0, 1.0]), np.diag([-1.0, 2.0])):
        try:
            matrix_logarithm(matrix)
        except MatrixFunctionError:
            pass
        else:
            raise AssertionError("invalid principal logarithm should be rejected")


def test_property_evidence_distinguishes_psd_pd_unitary_and_projection() -> None:
    positive = evidence_map(infer_properties(np.diag([1.0, 2.0, 3.0])))
    semidefinite = evidence_map(infer_properties(np.diag([0.0, 2.0, 3.0])))
    projection = evidence_map(infer_properties(np.diag([1.0, 0.0, 1.0])))
    assert positive["positive_definite"].supported is True
    assert semidefinite["positive_semidefinite"].supported is True
    assert semidefinite["positive_definite"].supported is False
    assert projection["projection"].supported is True
    assert positive["unitary"].supported is False
    assert positive["positive_definite"].formal_proof_claimed is False


def test_sparse_resource_envelopes_reject_oversized_operations() -> None:
    matrix = CSRMatrix.identity(4)
    try:
        matrix.to_dense(max_elements=4)
    except SparseError:
        pass
    else:
        raise AssertionError("dense conversion should respect max_elements")
