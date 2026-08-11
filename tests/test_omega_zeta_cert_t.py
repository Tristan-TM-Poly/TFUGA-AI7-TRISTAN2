import json

import pytest

from omega_millennium_t.r10.model import CELL_SCHEMA, CellRecord
from omega_zeta_cert_t.core import (
    classify_frontier,
    compile_problem_cells,
    effective_rank_diagnostic,
    rank_routes,
)
from omega_zeta_cert_t.model import BarrierClass, CertificateFamily, MomentTensorSpec
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


def test_moment_tensor_counts_symmetric_cross_observables():
    spec = MomentTensorSpec(max_order=4, window_count=3, base_support_radius=1.0)
    assert spec.observable_count == 34  # 3 + 6 + 10 + 15
    assert spec.conservative_support_radius == 4.0


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


def test_problem_cells_are_deterministic_and_oak_safe():
    bundle = default_bundle(0.70)
    a = compile_problem_cells(bundle)
    b = compile_problem_cells(bundle)
    assert a == b
    assert len({row["cell_id"] for row in a}) == len(a)
    assert {row["problem_id"] for row in a} == {"riemann"}
    assert {row["schema"] for row in a} == {CELL_SCHEMA}
    assert all(CellRecord.from_dict(row).to_dict() == row for row in a)
    serialized = json.dumps(a).lower()
    assert '"proof_claimed": true' not in serialized
    assert '"rh_solved_claimed": true' not in serialized


def test_mminus_is_retained_as_first_class_cells():
    cells = compile_problem_cells(default_bundle())
    mminus = [row for row in cells if row["front"] == "m-minus"]
    assert len(mminus) == 2
    assert all(row["payload"]["negative_evidence_retained"] for row in mminus)


def test_family_rejects_bound_above_declared_ceiling():
    bad = CertificateFamily("bad", 0.8, 0.7, 1.0)
    with pytest.raises(ValueError):
        bad.validate()
