from __future__ import annotations

import json

import pytest

from omega_emr_source_t import MECHANISMS, SpectrumTarget, audit_plan, classify_frequency, compile_source
from omega_emr_source_t.reporting import write_bundle


def test_frequency_classification_visible() -> None:
    result = classify_frequency(5e14)
    assert result.region == "visible"
    assert 5e-7 < result.wavelength_m < 7e-7
    assert result.photon_energy_ev < 10.0
    assert result.ionizing_candidate is False


def test_atlas_has_cross_spectrum_coverage() -> None:
    assert len(MECHANISMS) >= 20
    identifiers = {mechanism.mechanism_id for mechanism in MECHANISMS}
    assert "oscillating_charge_current" in identifiers
    assert "semiconductor_recombination" in identifiers
    assert "thermal_emission" in identifiers
    assert "bremsstrahlung" in identifiers
    assert "nuclear_transition" in identifiers


def test_low_power_visible_led_route_passes_oak() -> None:
    target = SpectrumTarget(
        center_frequency_hz=5e14,
        bandwidth_hz=2e13,
        power_w=1e-3,
        coherence="low",
        polarization="unpolarized",
        environment="shielded_lab",
        max_prototype_tier="low_power_benchtop",
    )
    plan = compile_source(target)
    identifiers = [candidate.mechanism_id for candidate in plan.recommended]
    assert "semiconductor_recombination" in identifiers
    assert plan.safety_status == "pass"
    assert audit_plan(plan).status == "pass"


def test_high_coherence_visible_route_contains_stimulated_emission() -> None:
    target = SpectrumTarget(
        center_frequency_hz=5e14,
        bandwidth_hz=1e9,
        power_w=1e-3,
        coherence="high",
        environment="simulation",
        max_prototype_tier="simulation_only",
    )
    plan = compile_source(target)
    identifiers = {candidate.mechanism_id for candidate in plan.recommended}
    assert "stimulated_emission_laser" in identifiers
    assert plan.safety_status == "simulation_only"
    assert plan.epistemic_status.endswith("pending_simulation")


def test_physical_xray_target_is_blocked_at_benchtop_tier() -> None:
    target = SpectrumTarget(
        center_frequency_hz=1e18,
        bandwidth_hz=1e17,
        power_w=1e-6,
        coherence="low",
        environment="shielded_lab",
        max_prototype_tier="low_power_benchtop",
    )
    plan = compile_source(target)
    assert plan.spectral_region == "x_ray"
    assert plan.ionizing_candidate is True
    assert plan.safety_status == "blocked"
    assert not plan.recommended
    assert audit_plan(plan).status == "blocked"


def test_xray_simulation_remains_available_without_build_permission() -> None:
    target = SpectrumTarget(
        center_frequency_hz=1e18,
        bandwidth_hz=2e17,
        power_w=1e-6,
        environment="simulation",
        max_prototype_tier="simulation_only",
    )
    plan = compile_source(target)
    assert plan.safety_status == "simulation_only"
    assert plan.recommended or plan.conditional
    assert any("no physical emission" in reason for reason in plan.safety_reasons)


def test_rf_without_radiating_authorization_requires_review() -> None:
    target = SpectrumTarget(
        center_frequency_hz=1e8,
        bandwidth_hz=1e6,
        power_w=1e-2,
        coherence="high",
        environment="shielded_lab",
        max_prototype_tier="low_power_benchtop",
        allow_radiating_output=False,
    )
    plan = compile_source(target)
    assert plan.safety_status == "review"
    assert any("matched dummy load" in control for control in plan.required_controls)
    assert audit_plan(plan).status == "review"


def test_compilation_is_deterministic() -> None:
    target = SpectrumTarget(
        center_frequency_hz=3e13,
        bandwidth_hz=5e12,
        power_w=1e-3,
        environment="simulation",
        max_prototype_tier="simulation_only",
    )
    assert compile_source(target).to_dict() == compile_source(target).to_dict()


def test_report_bundle_is_machine_readable(tmp_path) -> None:
    target = SpectrumTarget(
        center_frequency_hz=5e14,
        bandwidth_hz=1e13,
        power_w=1e-3,
        coherence="low",
        environment="shielded_lab",
    )
    plan = compile_source(target)
    oak = audit_plan(plan)
    paths = write_bundle(plan, oak, tmp_path)
    payload = json.loads((tmp_path / "source-plan.json").read_text(encoding="utf-8"))
    assert payload["spectral_region"] == "visible"
    assert set(paths) == {"source_plan", "oak_report", "markdown_report"}


def test_invalid_target_is_rejected() -> None:
    with pytest.raises(ValueError):
        SpectrumTarget(center_frequency_hz=0.0)
