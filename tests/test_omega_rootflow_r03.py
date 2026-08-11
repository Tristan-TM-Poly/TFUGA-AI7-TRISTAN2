import json

import numpy as np

from omega_rootflow_t import (
    ProjectiveRoot,
    basis_to_monomial,
    chordal_distance,
    conditioning_atlas,
    monomial_to_basis,
    native_root_jacobian,
    projective_roots,
    quadratic_square_root_loop,
    roots,
    track_coefficient_path,
)
from omega_rootflow_t.cli import main


def test_supported_basis_roundtrips_preserve_polynomial() -> None:
    coeffs = np.array([0.3, -1.2, 0.4, 1.0])
    for basis in ("monomial", "chebyshev", "legendre", "bernstein"):
        native = monomial_to_basis(coeffs, basis)
        reconstructed = basis_to_monomial(native, basis)
        assert np.allclose(reconstructed, coeffs, atol=1e-12)


def test_native_chebyshev_root_jacobian_matches_finite_coefficient_difference() -> None:
    power = np.array([-1.0, 0.2, 1.0])
    native = monomial_to_basis(power, "chebyshev")
    rr = roots(power)
    jac = native_root_jacobian(native, "chebyshev", rr)
    epsilon = 1e-7
    plus = native.copy()
    minus = native.copy()
    plus[0] += epsilon
    minus[0] -= epsilon
    plus_roots = roots(basis_to_monomial(plus, "chebyshev"))
    minus_roots = roots(basis_to_monomial(minus, "chebyshev"))
    # Quadratic roots remain naturally ordered for this tiny constant perturbation.
    numeric = (plus_roots - minus_roots) / (2.0 * epsilon)
    assert np.allclose(jac[:, 0], numeric, rtol=2e-6, atol=2e-7)


def test_conditioning_atlas_reconstructs_all_representations() -> None:
    atlas = conditioning_atlas([0.3, -1.2, 0.4, 1.0])
    assert len(atlas.records) == 4
    assert {record.basis for record in atlas.records} == {
        "monomial",
        "chebyshev",
        "legendre",
        "bernstein",
    }
    assert max(record.reconstruction_error for record in atlas.records) < 1e-12
    assert atlas.best_maximum_relative_condition_basis in {
        "monomial",
        "chebyshev",
        "legendre",
        "bernstein",
    }
    assert atlas.theorem_claimed is False


def test_projective_spectrum_preserves_nominal_degree_with_infinity_roots() -> None:
    spectrum = projective_roots([-1.0, 0.0, 1.0, 0.0, 0.0])
    assert spectrum.nominal_degree == 4
    assert spectrum.effective_degree == 2
    assert spectrum.infinity_multiplicity == 2
    assert np.allclose(np.sort_complex(spectrum.finite_roots), [-1.0, 1.0], atol=1e-12)
    assert sum(root.at_infinity for root in spectrum.roots) == 2
    assert spectrum.maximum_homogeneous_residual < 1e-12
    assert spectrum.status == "OAK_PROJECTIVE_DEGREE_TRANSITION"


def test_projective_chordal_distance_handles_infinity_without_divergence() -> None:
    zero = ProjectiveRoot(0j, 1.0 + 0j, False)
    infinity = ProjectiveRoot(1.0 + 0j, 0j, True)
    assert np.isclose(chordal_distance(zero, infinity), 1.0)


def test_square_root_loop_has_nontrivial_transposition_monodromy() -> None:
    result = track_coefficient_path(quadratic_square_root_loop(17), subdivisions=2)
    assert result.closed_coefficient_loop
    assert result.permutation == (1, 0)
    assert not result.is_identity
    assert result.maximum_corrected_residual < 1e-10
    assert result.minimum_derivative > 1.0
    assert result.status == "OAK_PASS_MONODROMY_LOOP"
    assert result.theorem_claimed is False


def test_r03_cli_basis_projective_and_monodromy_commands(tmp_path) -> None:
    basis_output = tmp_path / "basis.json"
    assert main(["basis-atlas", "--coeffs", "0.3,-1.2,0.4,1", "--output", str(basis_output)]) == 0
    basis_payload = json.loads(basis_output.read_text(encoding="utf-8"))
    assert basis_payload["version"] == "R0.3"
    assert len(basis_payload["atlas"]["records"]) == 4

    projective_output = tmp_path / "projective.json"
    assert main(
        ["projective", "--coeffs=-1,0,1,0,0", "--output", str(projective_output)]
    ) == 0
    projective_payload = json.loads(projective_output.read_text(encoding="utf-8"))
    assert projective_payload["spectrum"]["infinity_multiplicity"] == 2

    monodromy_output = tmp_path / "monodromy.json"
    assert main(
        [
            "monodromy-demo",
            "--samples",
            "17",
            "--subdivisions",
            "2",
            "--output",
            str(monodromy_output),
        ]
    ) == 0
    monodromy_payload = json.loads(monodromy_output.read_text(encoding="utf-8"))
    assert monodromy_payload["result"]["permutation"] == [1, 0]
    assert monodromy_payload["result"]["identity_monodromy"] is False
