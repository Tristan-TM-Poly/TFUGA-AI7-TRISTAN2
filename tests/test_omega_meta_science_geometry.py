from __future__ import annotations

import json
import subprocess
import sys

import pytest

from omega_meta_science_t.benchmark import build_fixture
from omega_meta_science_t.discovery import TheoryAdapter
from omega_meta_science_t.geometry import (
    ClaimConstraint,
    ScientificProgram,
    TransformCertificate,
    compile_adversarial_twin,
    empirical_theory_quotient,
    epistemic_hessian,
    evidence_independence,
    minimal_unsat_core,
    run_discovery_geometry_algebra_demo,
    scientific_superoptimize,
    validate_transform_certificate,
)


def test_theory_quotient_exposes_probe_dependence() -> None:
    theories = build_fixture().theories
    coarse = empirical_theory_quotient(theories, (0.0, 1.0))
    refined = empirical_theory_quotient(theories, (0.0, 1.0, 2.0))
    assert len(coarse.classes) == 1
    assert coarse.classes[0].member_ids == ("T_linear", "T_quadratic")
    assert len(refined.classes) == 2
    assert "declared probes only" in coarse.oak_boundary


def test_adversarial_twin_preserves_anchors_and_diverges_off_anchor() -> None:
    linear = build_fixture().theories[0]
    twin = compile_adversarial_twin(
        TheoryAdapter(linear),
        anchors=(0.0, 1.0),
        challenge_points=(2.0, 3.0),
        alphas=(-1.0, -0.5, 0.5, 1.0),
    )
    assert twin.max_anchor_error == pytest.approx(0.0)
    assert twin.strongest_challenge_x == 3.0
    assert twin.max_challenge_divergence == pytest.approx(6.0)
    assert "declared anchor-preserving" in twin.oak_boundary


def test_evidence_independence_discounts_correlated_support() -> None:
    report = evidence_independence(
        ("E1", "E2", "E3"),
        (
            (1.0, 0.9, 0.0),
            (0.9, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
    )
    assert report.matrix_valid is True
    assert report.raw_count == 3
    assert report.effective_count_surrogate == pytest.approx(1.875)
    assert 0.0 < report.redundancy_fraction < 1.0


def test_evidence_independence_fails_closed_on_invalid_matrix() -> None:
    report = evidence_independence(("E1", "E2"), ((1.0, 0.2), (0.8, 1.0)))
    assert report.matrix_valid is False
    assert report.effective_count_surrogate == 0.0
    assert any(error.startswith("matrix_not_symmetric") for error in report.errors)


def test_epistemic_hessian_matches_declared_quadratic_utility() -> None:
    def utility(point: tuple[float, ...]) -> float:
        a, b = point
        return -(a - 2.0) ** 2 - 2.0 * (b - 3.0) ** 2 + 0.5 * a * b

    report = epistemic_hessian(utility, (2.0, 3.0), step=1e-4, utility_name="toy")
    assert report.hessian[0][0] == pytest.approx(-2.0, rel=1e-5, abs=1e-5)
    assert report.hessian[1][1] == pytest.approx(-4.0, rel=1e-5, abs=1e-5)
    assert report.hessian[0][1] == pytest.approx(0.5, rel=1e-5, abs=1e-5)
    assert report.hessian[1][0] == pytest.approx(0.5, rel=1e-5, abs=1e-5)
    assert report.symmetry_residual == pytest.approx(0.0)
    assert "not curvature of truth" in report.oak_boundary


def test_claim_unsat_core_returns_smallest_declared_contradiction() -> None:
    report = minimal_unsat_core(
        (
            ClaimConstraint("C1", ("A", "B")),
            ClaimConstraint("C2", ("B", "C")),
            ClaimConstraint("C3", ("A", "C")),
        )
    )
    assert report.satisfiable is False
    assert report.minimal_core == ("C1", "C2", "C3")
    assert "declared finite world model" in report.oak_boundary


def test_claim_unsat_core_preserves_witness_when_satisfiable() -> None:
    report = minimal_unsat_core(
        (
            ClaimConstraint("C1", ("A", "B")),
            ClaimConstraint("C2", ("B", "C")),
        )
    )
    assert report.satisfiable is True
    assert report.witness_worlds == ("B",)
    assert report.minimal_core == ()


def test_proof_carrying_transform_fails_closed_on_loss() -> None:
    report = validate_transform_certificate(
        TransformCertificate(
            "bad",
            "A",
            "B",
            ("energy", "charge"),
            ("charge",),
            roundtrip_error=0.2,
            max_roundtrip_error=0.05,
            domain="declared",
            provenance="fixture:test",
        )
    )
    assert report.certified is False
    assert "roundtrip_error_exceeds_bound" in report.blockers
    assert "lost_invariant:energy" in report.blockers


def test_scientific_superoptimizer_applies_oak_before_cost() -> None:
    report = scientific_superoptimize(
        (
            ScientificProgram("baseline", ("a", "b", "c"), 10.0, 1.0, True, ("prov", "repro")),
            ScientificProgram("compressed", ("a", "c"), 4.0, 1.0, True, ("prov", "repro")),
            ScientificProgram("cheap_invalid", ("c",), 1.0, 0.1, False, ("prov",)),
        ),
        min_verified_gain=1.0,
        required_invariants=("prov", "repro"),
    )
    assert report.selected.program_id == "compressed"
    assert report.savings_vs_most_expensive_eligible == pytest.approx(6.0)
    rejected = dict(report.rejected)
    assert "oak_block" in rejected["cheap_invalid"]
    assert "missing_invariant:repro" in rejected["cheap_invalid"]


def test_r03_demo_composes_geometry_and_algebra_primitives() -> None:
    report = run_discovery_geometry_algebra_demo()
    assert len(report.quotient_coarse.classes) == 1
    assert len(report.quotient_refined.classes) == 2
    assert report.adversarial_twin.max_anchor_error == pytest.approx(0.0)
    assert report.evidence.effective_count_surrogate < report.evidence.raw_count
    assert report.unsat_core.satisfiable is False
    assert report.transform.certified is True
    assert report.superoptimizer.selected.program_id == "compressed"


def test_geometry_cli_replays_json() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "omega_meta_science_t.geometry_cli", "--compact"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert len(payload["quotient_coarse"]["classes"]) == 1
    assert len(payload["quotient_refined"]["classes"]) == 2
    assert payload["transform"]["certified"] is True
    assert payload["superoptimizer"]["selected"]["program_id"] == "compressed"
