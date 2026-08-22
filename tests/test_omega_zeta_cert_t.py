import json
from fractions import Fraction

import pytest

from omega_millennium_t.r10.model import CELL_SCHEMA, CellRecord
from omega_zeta_cert_t.core import (
    classify_frontier,
    compile_problem_cells,
    effective_rank_diagnostic,
    minimal_order_for_observable_budget,
    rank_routes,
)
from omega_zeta_cert_t.debt import (
    DebtStatus,
    DualSensitivity,
    compile_support_debt,
    compile_theorem_obligations,
    rank_sensitivities,
)
from omega_zeta_cert_t.dual import (
    RationalPolynomial,
    SpectralDualCertificate,
    moments_from_exact_spectrum,
    synthetic_dual_fixture,
)
from omega_zeta_cert_t.formal import build_finite_certificate_theorem_spec
from omega_zeta_cert_t.model import (
    BarrierClass,
    CertificateFamily,
    MomentTensorSpec,
    MomentWordMode,
    necklace_count,
)
from omega_zeta_cert_t.moments import (
    canonical_cyclic_word,
    cyclic_word_representatives,
    moment_coordinate_labels,
    noncommutative_trace_countermodel,
)
from omega_zeta_cert_t.presets import ANTHROPIC_2026_FAMILY, default_bundle


def test_external_family_is_fail_closed_and_has_small_headroom():
    family = ANTHROPIC_2026_FAMILY
    family.validate()
    assert family.current_bound == pytest.approx(0.6725)
    assert family.method_ceiling == pytest.approx(0.6818)
    assert family.headroom == pytest.approx(0.0093)


def test_target_above_ceiling_requires_new_arithmetic_information():
    bundle = default_bundle(0.70)
    decision = classify_frontier(bundle.family, 0.70, moment_spec=bundle.moment_spec)
    assert not decision.attainable_inside_declared_family
    assert decision.barrier is BarrierClass.NEW_ARITHMETIC_INFORMATION
    assert decision.gap_beyond_ceiling == pytest.approx(0.0182)
    assert decision.required_support_radius_hint == pytest.approx(4.0)


def test_target_below_ceiling_does_not_claim_attainment():
    decision = classify_frontier(ANTHROPIC_2026_FAMILY, 0.675)
    assert decision.attainable_inside_declared_family
    assert decision.barrier is BarrierClass.WINDOW_OPTIMIZATION
    assert "does not establish existence" in decision.claim_boundary


def test_symmetric_r01_count_remains_available_as_explicit_mode():
    spec = MomentTensorSpec(
        max_order=4,
        window_count=3,
        base_support_radius=1.0,
        word_mode=MomentWordMode.SYMMETRIC,
    )
    assert spec.order_counts == (3, 6, 10, 15)
    assert spec.observable_count == 34


def test_cyclic_noncommutative_count_is_44_for_three_windows_through_order_four():
    spec = MomentTensorSpec(
        max_order=4,
        window_count=3,
        base_support_radius=1.0,
        word_mode=MomentWordMode.CYCLIC,
    )
    assert spec.order_counts == (3, 6, 11, 24)
    assert spec.observable_count == 44
    assert spec.conservative_support_radius == 4.0


def test_full_noncommutative_count_is_120():
    spec = MomentTensorSpec(
        max_order=4,
        window_count=3,
        base_support_radius=1.0,
        word_mode=MomentWordMode.FULL,
    )
    assert spec.order_counts == (3, 9, 27, 81)
    assert spec.observable_count == 120


@pytest.mark.parametrize(
    ("length", "expected"),
    [(1, 3), (2, 6), (3, 11), (4, 24)],
)
def test_necklace_formula_matches_materialized_cyclic_classes(length, expected):
    assert necklace_count(3, length) == expected
    assert len(cyclic_word_representatives(3, length)) == expected


def test_canonical_cyclic_word_identifies_rotations_but_not_arbitrary_permutations():
    assert canonical_cyclic_word((0, 1, 2)) == canonical_cyclic_word((1, 2, 0))
    assert canonical_cyclic_word((0, 1, 2)) != canonical_cyclic_word((0, 2, 1))


def test_exact_countermodel_preserves_cyclic_trace_and_breaks_full_symmetry():
    court = noncommutative_trace_countermodel()
    assert court.tr_abc == court.tr_bca == court.tr_cab == 1
    assert court.tr_acb == 0
    assert court.cyclic_invariance_holds
    assert court.arbitrary_permutation_invariance_fails
    assert not court.proof_claimed


def test_default_bundle_uses_oak_safe_cyclic_word_mode():
    spec = default_bundle().moment_spec
    assert spec is not None
    assert spec.word_mode is MomentWordMode.CYCLIC
    assert spec.observable_count == 44


def test_moment_coordinate_labels_are_deterministic_and_complete():
    spec = default_bundle().moment_spec
    labels_a = moment_coordinate_labels(spec)
    labels_b = moment_coordinate_labels(spec)
    assert labels_a == labels_b
    assert len(labels_a) == 44
    assert len(set(labels_a)) == 44


def test_support_debt_separates_declared_budget_from_conservative_extension():
    spec = default_bundle().moment_spec
    debt = compile_support_debt(spec, declared_known_radius=1.0)
    assert debt[0].status is DebtStatus.INSIDE_DECLARED_BUDGET
    assert [row.conservative_required_radius for row in debt] == [1.0, 2.0, 3.0, 4.0]
    assert all(row.status is DebtStatus.REQUIRES_NEW_OR_REDUCED_SUPPORT_INPUT for row in debt[1:])
    assert all(not row.to_dict()["proof_claimed"] for row in debt)


def test_theorem_debt_for_target_070_contains_ceiling_support_and_compression_gates():
    bundle = default_bundle(0.70)
    obligations = compile_theorem_obligations(bundle.family, bundle.target_bound, bundle.moment_spec)
    ids = {row.obligation_id for row in obligations}
    assert "zeta-cross-declared-family-ceiling" in ids
    assert "zeta-discharge-support-debt" in ids
    assert "zeta-no-unjustified-full-symmetrization" in ids
    assert "zeta-polynomial-dual-domain-control" in ids
    assert all(not row.to_dict()["proof_claimed"] for row in obligations)


def test_below_ceiling_drops_required_cross_ceiling_obligation():
    bundle = default_bundle(0.675)
    obligations = compile_theorem_obligations(bundle.family, bundle.target_bound, bundle.moment_spec)
    assert "zeta-cross-declared-family-ceiling" not in {row.obligation_id for row in obligations}


def test_dual_sensitivity_requires_caller_supplied_multiplier_and_is_not_truth_probability():
    item = DualSensitivity(
        observable_id="M4:cyc[0,1,0,2]",
        dual_multiplier=-2.0,
        anticipated_observable_improvement=0.03,
        theorem_cost=0.2,
        source_class="synthetic_dual_fixture",
    )
    assert item.shadow_value == pytest.approx(0.06)
    assert item.theorem_voi == pytest.approx(0.3)
    row = item.to_dict()
    assert row["score_semantics"] == "sensitivity_per_declared_cost_not_truth_probability"
    assert not row["proof_claimed"]


def test_sensitivity_ranking_is_deterministic():
    a = DualSensitivity("M3", 1.0, 0.1, 0.5, "fixture")
    b = DualSensitivity("M4", 2.0, 0.1, 0.5, "fixture")
    assert [x.observable_id for x in rank_sensitivities((a, b))] == ["M4", "M3"]


def test_effective_rank_is_scale_invariant_but_not_promoted_to_zeta_theorem():
    a = effective_rank_diagnostic(6.0, 14.0)
    b = effective_rank_diagnostic(12.0, 56.0)
    assert a == pytest.approx(b)
    assert a == pytest.approx(36 / 14)


def test_effective_rank_rejects_invalid_second_moment():
    with pytest.raises(ValueError):
        effective_rank_diagnostic(1.0, 0.0)


def test_routes_are_deterministically_ranked_and_scores_are_not_probabilities():
    routes = rank_routes(default_bundle().routes)
    assert [r.route_id for r in routes] == [r.route_id for r in rank_routes(list(reversed(routes)))]
    assert all(-1.0 <= route.voi_score <= 1.0 for route in routes)
    assert "theorem-debt-compiler" in {route.route_id for route in routes}


def test_minimal_order_uses_requested_word_mode():
    assert minimal_order_for_observable_budget(
        3, 35, word_mode=MomentWordMode.SYMMETRIC
    ) == 5
    assert minimal_order_for_observable_budget(
        3, 35, word_mode=MomentWordMode.CYCLIC
    ) == 4


def test_problem_cells_are_deterministic_r10_compatible_and_oak_safe():
    bundle = default_bundle(0.70)
    a = compile_problem_cells(bundle)
    b = compile_problem_cells(bundle)
    assert a == b
    assert len({row["cell_id"] for row in a}) == len(a)
    assert {row["problem_id"] for row in a} == {"riemann"}
    assert {row["schema"] for row in a} == {CELL_SCHEMA}
    assert all(CellRecord.from_dict(row).to_dict() == row for row in a)
    fronts = {row["front"] for row in a}
    assert {
        "barrier",
        "representation",
        "support-debt",
        "theorem-debt",
        "countermodel",
        "verification-fixture",
        "formal-obligation",
        "research-route",
        "m-minus",
    }.issubset(fronts)
    serialized = json.dumps(a).lower()
    assert '"proof_claimed": true' not in serialized
    assert '"rh_solved_claimed": true' not in serialized


def test_noncommutative_mminus_is_retained_as_first_class_cell():
    cells = compile_problem_cells(default_bundle())
    mminus = [row for row in cells if row["front"] == "m-minus"]
    ids = {row["payload"]["record_id"] for row in mminus}
    assert "m-zeta-full-symmetrization-003" in ids
    assert all(row["payload"]["negative_evidence_retained"] for row in mminus)


def test_countermodel_cell_is_exact_and_not_promoted():
    cells = compile_problem_cells(default_bundle())
    counter = [row for row in cells if row["front"] == "countermodel"]
    assert len(counter) == 1
    assert counter[0]["payload"]["cyclic_invariance_holds"]
    assert counter[0]["payload"]["arbitrary_permutation_invariance_fails"]
    assert not counter[0]["payload"]["proof_claimed"]


def test_family_rejects_bound_above_declared_ceiling():
    bad = CertificateFamily("bad", 0.8, 0.7, 1.0)
    with pytest.raises(ValueError):
        bad.validate()


def test_exact_bernstein_dual_fixture_certifies_only_its_finite_scope():
    fixture = synthetic_dual_fixture()
    row = fixture.to_dict()
    assert row["polynomial_constraints_certified"]
    assert row["lower_bound_certified"]
    assert row["certified_lower_bound"] == "1/3"
    assert row["certificate_scope"] == "finite_exact_moment_problem_under_supplied_proven_spectral_domain"
    assert not row["zeta_theorem_claimed"]
    assert not row["rh_solved_claimed"]


def test_dual_certificate_fails_closed_without_proven_domain_control():
    polynomial = RationalPolynomial.from_values((0, 1))
    moments = moments_from_exact_spectrum((-1, 1, 1), 1)
    candidate = SpectralDualCertificate(
        polynomial=polynomial,
        spectral_radius=Fraction(1),
        normalized_moments=moments,
        domain_control_proven=False,
        domain_control_source="unproven_zeta_operator_norm_placeholder",
    )
    row = candidate.to_dict()
    assert row["polynomial_constraints_certified"]
    assert not row["lower_bound_certified"]
    assert row["certified_lower_bound"] is None


def test_bernstein_checker_rejects_polynomial_positive_at_zero_on_negative_side():
    polynomial = RationalPolynomial.from_values((Fraction(1, 2), 1))
    candidate = SpectralDualCertificate(
        polynomial=polynomial,
        spectral_radius=Fraction(1),
        normalized_moments=(Fraction(1), Fraction(0)),
        domain_control_proven=True,
        domain_control_source="synthetic",
    )
    assert not candidate.negative_side_check().nonnegative_certified
    assert not candidate.lower_bound_certified


def test_exact_spectrum_moments_are_rational_and_normalized():
    moments = moments_from_exact_spectrum((-1, 1, 1), 4)
    assert moments == (
        Fraction(1),
        Fraction(1, 3),
        Fraction(1),
        Fraction(1, 3),
        Fraction(1),
    )


def test_formal_spec_is_explicitly_not_kernel_checked_or_proven():
    spec = build_finite_certificate_theorem_spec(synthetic_dual_fixture())
    row = spec.to_dict()
    assert row["backend_target"] == "Lean4/mathlib"
    assert row["status"] == "theorem_spec_only"
    assert not row["kernel_checked"]
    assert not row["proof_claimed"]
    assert not row["rh_solved_claimed"]


def test_problem_cells_include_exact_dual_fixture_and_formal_obligation_without_zeta_promotion():
    cells = compile_problem_cells(default_bundle())
    verification = [row for row in cells if row["front"] == "verification-fixture"]
    formal = [row for row in cells if row["front"] == "formal-obligation"]
    assert len(verification) == 1
    assert verification[0]["payload"]["certified_lower_bound"] == "1/3"
    assert verification[0]["payload"]["fixture_semantics"] == "synthetic_exact_kernel_test_not_zeta_evidence"
    assert len(formal) == 1
    assert formal[0]["payload"]["status"] == "theorem_spec_only"
    assert not formal[0]["payload"]["kernel_checked"]


def test_r02_reference_fixture_matches_runtime():
    from pathlib import Path
    from collections import Counter

    reference = json.loads(Path("data/omega_zeta_cert/r02_reference.json").read_text())
    bundle = default_bundle(reference["target_bound"])
    cells = compile_problem_cells(bundle)
    decision = classify_frontier(bundle.family, bundle.target_bound, moment_spec=bundle.moment_spec)

    assert reference["bundle_digest"] == bundle.digest
    assert reference["moment_word_mode"] == bundle.moment_spec.word_mode.value
    assert reference["moment_order_counts"] == list(bundle.moment_spec.order_counts)
    assert reference["moment_observable_count"] == bundle.moment_spec.observable_count
    assert reference["frontier_barrier"] == decision.barrier.value
    assert reference["cell_count"] == len(cells)
    assert reference["front_counts"] == dict(sorted(Counter(row["front"] for row in cells).items()))
    assert reference["countermodel"] == noncommutative_trace_countermodel().to_dict()
    assert reference["dual_fixture"]["certified_lower_bound"] == synthetic_dual_fixture().to_dict()["certified_lower_bound"]
    assert reference["proof_claimed"] is False
    assert reference["rh_solved_claimed"] is False
