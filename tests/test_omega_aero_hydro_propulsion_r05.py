from __future__ import annotations

import pytest

from omega_aero_hydro_propulsion_t.architecture_compiler import (
    PropulsionMissionIntent,
    compile_propulsion_architectures,
    default_architecture_templates,
    infer_domain,
)
from omega_aero_hydro_propulsion_t.evidence_ladder import (
    EvidenceReceipt,
    assess_evidence_ladder,
    assess_receipt,
    computational_receipts,
)
from omega_aero_hydro_propulsion_t.models import OperatingPoint, default_air, default_water, demo_rotor
from omega_aero_hydro_propulsion_t.r05_oak import demo_air_intent, demo_water_intent, run_r05_benchmarks
from omega_aero_hydro_propulsion_t.wake_graph import (
    Vector3,
    VortexSegment,
    WakeConfig,
    analyze_wake_graph,
    induced_velocity_from_segment,
)


def test_wake_graph_cardinality_and_determinism():
    design = demo_rotor()
    config = WakeConfig(revolutions=1.0, segments_per_revolution=8)
    operating = OperatingPoint(freestream_velocity=22.0, rpm=2_200.0)
    left = analyze_wake_graph(design, default_air(), operating, config=config)
    right = analyze_wake_graph(design, default_air(), operating, config=config)
    expected = len(left.bem.sections) * design.blade_count * config.step_count
    assert len(left.segments) == expected
    assert left.evidence_hash == right.evidence_hash
    assert left.to_dict() == right.to_dict()
    assert left.finite
    assert left.physics_certified is False
    assert left.physical_fidelity_claim is False


def test_stationary_rotor_has_no_vortex_wake():
    report = analyze_wake_graph(
        demo_rotor(),
        default_air(),
        OperatingPoint(freestream_velocity=15.0, rpm=0.0),
        config=WakeConfig(revolutions=1.0, segments_per_revolution=8),
    )
    assert report.nodes == ()
    assert report.segments == ()
    assert report.filament_count == 0
    assert report.maximum_probe_speed == 0.0
    assert all(probe.induced_velocity == Vector3(0.0, 0.0, 0.0) for probe in report.probes)


def test_regularized_segment_endpoint_is_finite_and_zero():
    segment = VortexSegment(
        filament_id="test",
        segment_index=0,
        blade_index=0,
        source_radius=1.0,
        circulation=2.0,
        core_radius=0.05,
        start=Vector3(0.0, 0.0, 0.0),
        end=Vector3(1.0, 0.0, 0.0),
    )
    assert induced_velocity_from_segment(segment.start, segment) == Vector3(0.0, 0.0, 0.0)
    off_axis = induced_velocity_from_segment(Vector3(0.5, 1.0, 0.0), segment)
    assert off_axis.norm > 0.0
    assert off_axis.z != 0.0


def test_wake_config_rejects_singular_settings():
    with pytest.raises(ValueError):
        WakeConfig(segments_per_revolution=4).validate()
    with pytest.raises(ValueError):
        WakeConfig(core_radius_fraction=0.0).validate()
    with pytest.raises(ValueError):
        WakeConfig(contraction_ratio=0.5).validate()


def test_architecture_templates_are_unique_and_valid():
    templates = default_architecture_templates()
    ids = [item.architecture_id for item in templates]
    assert len(ids) == len(set(ids))
    for item in templates:
        item.validate()


def test_air_and_water_domain_routing():
    assert infer_domain(default_air()) == "air"
    assert infer_domain(default_water()) == "water"
    air = compile_propulsion_architectures(demo_air_intent(), default_air())
    water = compile_propulsion_architectures(demo_water_intent(), default_water())
    assert air.best is not None
    assert water.best is not None
    assert all(item.architecture.domain == "air" for item in air.candidates if item.eligible)
    assert all(item.architecture.domain == "water" for item in water.candidates if item.eligible)
    assert air.permanent_total_cap is None
    assert water.permanent_total_cap is None
    assert air.physics_certified is False
    assert water.physics_certified is False


def test_architecture_compiler_is_deterministic():
    left = compile_propulsion_architectures(demo_air_intent(), default_air())
    right = compile_propulsion_architectures(demo_air_intent(), default_air())
    assert left.evidence_hash == right.evidence_hash
    assert left.ranked_eligible_ids == right.ranked_eligible_ids
    assert left.to_dict() == right.to_dict()


def test_architecture_constraints_can_reject_all_candidates():
    mission = PropulsionMissionIntent(
        mission_id="impossible-installation",
        required_thrust_n=100_000.0,
        cruise_velocity_mps=50.0,
        installation_area_m2=0.001,
        redundancy_priority=1.0,
        efficiency_priority=1.0,
        acoustic_priority=1.0,
        compactness_priority=1.0,
        maintainability_priority=1.0,
        vectoring_priority=1.0,
    )
    report = compile_propulsion_architectures(mission, default_air())
    assert report.best is None
    assert not report.ranked_eligible_ids
    assert all(not item.eligible for item in report.candidates)


def test_computational_receipts_form_contiguous_f3_ladder():
    wake = analyze_wake_graph(
        demo_rotor(),
        default_air(),
        OperatingPoint(freestream_velocity=22.0, rpm=2_200.0),
        config=WakeConfig(revolutions=1.0, segments_per_revolution=8),
    )
    report = assess_evidence_ladder(computational_receipts(wake_hash=wake.evidence_hash))
    assert report.highest_supported_tier == "F3_VORTEX_PROXY"
    assert report.contiguous_tier == "F3_VORTEX_PROXY"
    assert not report.missing_lower_tiers
    assert report.certification_claim is False
    assert report.physics_certified is False


def test_high_tier_without_lower_evidence_is_not_contiguous():
    receipt = EvidenceReceipt(
        receipt_id="isolated-f3",
        tier="F3_VORTEX_PROXY",
        artifact_sha256="1" * 64,
        provenance="test",
        method="vortex proxy",
        limitations=("isolated receipt",),
        metadata={
            "vortex_model": "finite segment",
            "core_model": "regularized",
            "discretization": "test",
        },
    )
    report = assess_evidence_ladder((receipt,))
    assert report.highest_supported_tier == "F3_VORTEX_PROXY"
    assert report.contiguous_tier is None
    assert report.missing_lower_tiers == ("F0_ANALYTIC", "F1_SYSTEM", "F2_STRESS")


def test_phantom_cfd_receipt_is_blocked():
    receipt = EvidenceReceipt(
        receipt_id="bad-cfd",
        tier="F4_HIGH_FIDELITY_NUMERICAL",
        artifact_sha256="2" * 64,
        provenance="test",
        method="claimed CFD",
        limitations=("negative control",),
        metadata={
            "solver": "unknown",
            "governing_equations": "unspecified",
            "boundary_conditions": "unspecified",
            "mesh_levels": 1,
            "residual_converged": False,
        },
    )
    assessment = assess_receipt(receipt)
    assert not assessment.accepted
    assert "mesh_independence_requires_at_least_three_levels" in assessment.blockers
    assert "residual_convergence_not_demonstrated" in assessment.blockers


def test_experiment_without_raw_data_is_blocked():
    receipt = EvidenceReceipt(
        receipt_id="bad-experiment",
        tier="F5_EXPERIMENT",
        artifact_sha256="3" * 64,
        provenance="test",
        method="bench experiment",
        limitations=("negative control",),
        metadata={
            "facility": "synthetic",
            "instrumentation": "synthetic",
            "calibration_id": "none",
            "uncertainty_budget": "",
            "raw_data_retained": False,
        },
    )
    assessment = assess_receipt(receipt)
    assert not assessment.accepted
    assert "raw_data_not_retained" in assessment.blockers
    assert "uncertainty_budget_missing" in assessment.blockers


def test_receipt_cannot_claim_certification():
    with pytest.raises(ValueError, match="cannot assert certification"):
        EvidenceReceipt(
            receipt_id="invalid-certification",
            tier="F6_ENGINEERING_REVIEW",
            artifact_sha256="4" * 64,
            provenance="test",
            method="invalid",
            limitations=("test",),
            metadata={},
            certification_claim=True,
        ).validate()


def test_duplicate_receipt_ids_are_rejected():
    receipt = EvidenceReceipt(
        receipt_id="duplicate",
        tier="F0_ANALYTIC",
        artifact_sha256="5" * 64,
        provenance="test",
        method="analytic",
        limitations=("test",),
        metadata={"equations": "test", "assumptions": "test"},
    )
    with pytest.raises(ValueError, match="unique"):
        assess_evidence_ladder((receipt, receipt))


def test_r05_oak_benchmarks_pass():
    report = run_r05_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_WAKE_ARCHITECTURE_EVIDENCE_R0_5"
    assert report.physics_certified is False
