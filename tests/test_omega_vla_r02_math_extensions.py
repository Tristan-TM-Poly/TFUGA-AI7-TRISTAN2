from pathlib import Path

import numpy as np

from omega_vla_t.r02 import (
    FiniteChainComplex,
    FrontierCodec,
    LeanTargetCompiler,
    TheoremFactory,
    build_linearization_atlas,
    build_linearization_cell,
    filled_oriented_triangle,
    oriented_cycle_incidence,
)


def test_cycle_chain_complex_has_one_harmonic_one_form() -> None:
    boundary_1 = oriented_cycle_incidence(5)
    complex_ = FiniteChainComplex((boundary_1,))
    audit = complex_.audit()
    assert audit.valid
    assert complex_.dimensions == (5, 5)
    assert complex_.betti_number(0) == 1
    assert complex_.betti_number(1) == 1

    flow = np.ones(5)
    report = complex_.hodge_decomposition(1, flow)
    assert report.betti_number == 1
    assert report.reconstruction_error < 1e-12
    assert report.harmonic_laplacian_residual < 1e-10
    assert np.linalg.norm(report.exact) < 1e-10
    assert np.allclose(report.harmonic, flow)
    assert report.theorem_claimed is False


def test_filled_triangle_removes_first_homology() -> None:
    complex_ = filled_oriented_triangle()
    assert complex_.audit().valid
    assert complex_.dimensions == (3, 3, 1)
    assert complex_.betti_number(0) == 1
    assert complex_.betti_number(1) == 0
    assert complex_.betti_number(2) == 0

    edge_flow = np.ones(3)
    report = complex_.hodge_decomposition(1, edge_flow)
    assert report.reconstruction_error < 1e-12
    assert report.harmonic_laplacian_residual < 1e-10
    assert np.linalg.norm(report.harmonic) < 1e-10
    assert np.allclose(report.coexact, edge_flow)


def test_chain_complex_rejects_boundary_of_boundary_failure() -> None:
    boundary_1 = oriented_cycle_incidence(3)
    bad_boundary_2 = np.array([[1.0], [0.0], [0.0]])
    try:
        FiniteChainComplex((boundary_1, bad_boundary_2))
    except ValueError as exc:
        assert "boundary-of-boundary" in str(exc)
    else:
        raise AssertionError("invalid chain complex should be rejected")


def test_hodge_laplacian_is_symmetric_positive_semidefinite() -> None:
    complex_ = filled_oriented_triangle()
    for degree in range(3):
        laplacian = complex_.hodge_laplacian(degree)
        assert np.allclose(laplacian, laplacian.T)
        assert np.min(np.linalg.eigvalsh(laplacian)) > -1e-12


def test_lean_target_is_explicitly_incomplete() -> None:
    codec = FrontierCodec()
    cell = TheoremFactory().generate(codec.decode(codec.sample_indices(1, seed=4)[0]))
    target = LeanTargetCompiler().compile(cell)
    assert target.source_cell_id == cell.cell_id
    assert target.language == "Lean4"
    assert target.proof_status == "FORMALIZED_INCOMPLETE"
    assert target.sorry_count == 1
    assert "sorry" in target.code
    assert "Natural-language assumptions" in target.code
    assert target.theorem_claimed is False
    assert target.formally_verified is False


def test_lean_bundle_is_deterministic_and_claim_safe(tmp_path: Path) -> None:
    codec = FrontierCodec()
    factory = TheoremFactory()
    cells = [factory.generate(address) for address in codec.iter_sample(4, seed=11)]
    compiler = LeanTargetCompiler()
    first_targets = compiler.compile_many(cells)
    second_targets = compiler.compile_many(cells)
    assert first_targets == second_targets

    manifest = compiler.write_bundle(first_targets, tmp_path)
    assert manifest.targets == 4
    assert manifest.theorem_claimed is False
    assert manifest.formal_proof_claimed is False
    assert len(manifest.aggregate_sha256) == 64
    assert (tmp_path / "manifest.json").exists()
    assert len(list(tmp_path.glob("*.lean"))) == 4
    assert len(list(tmp_path.glob("*.lean.json"))) == 4


def nonlinear_fixture(x: np.ndarray) -> np.ndarray:
    return np.array(
        [
            x[0] ** 2 + x[1],
            np.sin(x[0]) + 0.25 * x[1] ** 2,
        ]
    )


def test_linearization_cell_measures_radius_dependent_residual() -> None:
    center = np.array([0.25, -0.1])
    small = build_linearization_cell(
        nonlinear_fixture,
        center,
        radius=1e-3,
        validity_tolerance=1e-3,
        random_directions=8,
        seed=3,
    )
    large = build_linearization_cell(
        nonlinear_fixture,
        center,
        radius=0.25,
        validity_tolerance=1.0,
        random_directions=8,
        seed=3,
    )
    assert small.maximum_absolute_residual < large.maximum_absolute_residual
    assert small.maximum_relative_residual < large.maximum_relative_residual
    assert small.sample_count == 12
    assert small.theorem_claimed is False
    assert small.scientific_validation_claimed is False


def test_linearization_atlas_builds_overlap_graph_and_prediction() -> None:
    centers = [
        np.array([0.0, 0.0]),
        np.array([0.1, 0.0]),
        np.array([1.0, 1.0]),
    ]
    atlas = build_linearization_atlas(
        nonlinear_fixture,
        centers,
        radii=[0.08, 0.08, 0.05],
        validity_tolerance=0.1,
        random_directions=4,
        seed=19,
    )
    assert len(atlas.cells) == 3
    assert atlas.input_dimension == 2
    assert atlas.output_dimension == 2
    assert len(atlas.transitions) == 2
    assert atlas.coverage_claimed is False
    assert atlas.theorem_claimed is False

    point = np.array([0.02, -0.01])
    prediction, cell, valid = atlas.predict(point)
    observed = nonlinear_fixture(point)
    assert prediction.shape == observed.shape
    assert np.linalg.norm(prediction - observed) < 0.01
    assert cell.cell_id == atlas.cells[0].cell_id
    assert isinstance(valid, bool)


def test_linearization_atlas_rejects_incompatible_centers() -> None:
    try:
        build_linearization_atlas(
            nonlinear_fixture,
            [np.zeros(2), np.zeros(3)],
            radii=0.1,
        )
    except ValueError as exc:
        assert "dimension" in str(exc)
    else:
        raise AssertionError("mixed center dimensions should fail")
