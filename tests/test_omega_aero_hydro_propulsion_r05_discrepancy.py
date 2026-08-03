from __future__ import annotations

import pytest

from omega_aero_hydro_propulsion_t.evidence_discrepancy import (
    MetricObservation,
    build_discrepancy_tensor,
    demo_discrepancy_tensor,
)


def test_demo_discrepancy_tensor_is_deterministic_and_non_promotional():
    left = demo_discrepancy_tensor()
    right = demo_discrepancy_tensor()
    assert left.to_dict() == right.to_dict()
    assert left.evidence_hash == right.evidence_hash
    assert left.metric_count == 2
    assert left.comparison_count == 2
    assert left.physics_certified is False
    assert left.automatic_model_promotion is False


def test_discrepancy_normalizes_by_combined_uncertainty():
    report = build_discrepancy_tensor(
        (
            MetricObservation("low", "F0_ANALYTIC", "thrust", 100.0, "N", 3.0, "a" * 64, "low-order"),
            MetricObservation("high", "F3_VORTEX_PROXY", "thrust", 110.0, "N", 4.0, "b" * 64, "proxy"),
        )
    )
    comparison = report.comparisons[0]
    assert comparison.combined_standard_uncertainty == 5.0
    assert comparison.normalized_residual == 2.0
    assert comparison.exceeds_two_sigma is False
    assert comparison.relative_delta == 0.1


def test_zero_uncertainty_does_not_invent_infinite_significance():
    report = build_discrepancy_tensor(
        (
            MetricObservation("low", "F0_ANALYTIC", "power", 10.0, "W", 0.0, "c" * 64, "fixture"),
            MetricObservation("high", "F1_SYSTEM", "power", 12.0, "W", 0.0, "d" * 64, "fixture"),
        )
    )
    comparison = report.comparisons[0]
    assert comparison.normalized_residual is None
    assert comparison.exceeds_two_sigma is None


def test_unit_mismatch_is_blocked():
    with pytest.raises(ValueError, match="unit mismatch"):
        build_discrepancy_tensor(
            (
                MetricObservation("n", "F0_ANALYTIC", "thrust", 100.0, "N", 1.0, "e" * 64, "fixture"),
                MetricObservation("lbf", "F1_SYSTEM", "thrust", 22.0, "lbf", 1.0, "f" * 64, "fixture"),
            )
        )


def test_duplicate_observation_ids_are_blocked():
    observation = MetricObservation("duplicate", "F0_ANALYTIC", "thrust", 100.0, "N", 1.0, "1" * 64, "fixture")
    with pytest.raises(ValueError, match="unique"):
        build_discrepancy_tensor((observation, observation))


def test_negative_uncertainty_is_blocked():
    with pytest.raises(ValueError, match="uncertainty"):
        MetricObservation("bad", "F0_ANALYTIC", "thrust", 100.0, "N", -1.0, "2" * 64, "fixture").validate()
