from math import cos, pi, sin

import pytest

from omega_generator_discovery_t import (
    ExperimentCandidate,
    compare_spectra,
    compile_morph_ir,
    compile_protocol,
    crystal_holonomy,
    design_order_experiment,
    evidence_growth_transition,
    fit_scalar_generator,
    front_registry,
    generator_syndrome,
    identify_affine_1d,
    lorentzian,
    prioritize_experiments,
    semigroup_defect,
)


def test_identifies_affine_translation_and_scale():
    result = identify_affine_1d([0, 1, 2, 3], [2, 5, 8, 11])
    assert result.scale == pytest.approx(3.0)
    assert result.translation == pytest.approx(2.0)
    assert result.relative_residual < 1e-12


def test_scalar_generator_predicts():
    result = fit_scalar_generator([1, 3, 7, 15])
    assert result.multiplier == pytest.approx(2.0)
    assert result.forcing == pytest.approx(1.0)
    assert result.predict(15) == pytest.approx(31.0)


def test_semigroup_defect_detects_consistency():
    one = ((2.0, 0.0), (0.0, 0.5))
    two = ((4.0, 0.0), (0.0, 0.25))
    assert semigroup_defect(one, two) < 1e-12


def test_order_experiment_detects_noncommutation():
    a = ((1.0, 1.0), (0.0, 1.0))
    b = ((1.0, 0.0), (1.0, 1.0))
    report = design_order_experiment(a, b)
    assert report.normalized_order_effect > 0
    assert report.commutator_norm > 0


def test_generator_syndrome_classifies_drift():
    expected = ((1.0, 0.0), (0.0, 1.0))
    observed = ((1.01, 0.0), (0.0, 1.0))
    assert generator_syndrome(expected, observed).classification == "continuous_drift_candidate"


def test_spectral_shift_candidate():
    axis = [i*0.1 for i in range(-100, 101)]
    before = lorentzian(axis, area=1.0, center=0.0, hwhm=0.5)
    after = lorentzian(axis, area=1.0, center=1.0, hwhm=0.5)
    result = compare_spectra(axis, before, after)
    assert result.centroid_shift == pytest.approx(1.0, abs=0.15)


def test_crystal_closed_loop_has_small_holonomy():
    q0 = (1.0, 0.0, 0.0, 0.0)
    q1 = (cos(pi/8), 0.0, 0.0, sin(pi/8))
    q2 = (cos(pi/4), 0.0, 0.0, sin(pi/4))
    result = crystal_holonomy([q0, q1, q2])
    assert result.residual_angle_radians < 1e-7


def test_epistemic_growth_flags_expansion_without_evidence():
    result = evidence_growth_transition(
        concepts_before=10, concepts_after=20, evidence_before=4, evidence_after=4
    )
    assert result.classification == "concept_expansion_without_new_evidence"


def test_autolab_blocks_irreversible_candidate():
    decisions = prioritize_experiments([
        ExperimentCandidate("safe", 0.8, 0.7, 0.6, 0.2, 0.1, True),
        ExperimentCandidate("unsafe", 1.0, 1.0, 1.0, 0.1, 0.1, False),
    ])
    lookup = {item.name: item for item in decisions}
    assert lookup["safe"].approved_for_autonomous_draft
    assert not lookup["unsafe"].approved_for_autonomous_draft


def test_protocol_requires_rollback():
    with pytest.raises(ValueError):
        compile_protocol({"instrument_id": "raman", "outputs": ["spectrum"]})


def test_protocol_and_morph_ir_compile():
    protocol = compile_protocol({
        "instrument_id": "raman",
        "inputs": ["laser_power"],
        "outputs": ["spectrum"],
        "generators": ["acquisition"],
        "safety_limits": {"laser_power": 10},
        "rollback_steps": ["restore_previous_power"],
    })
    assert protocol.instrument_id == "raman"
    ir = compile_morph_ir({
        "name": "spectral_shift",
        "domain": "spectrum",
        "codomain": "spectrum",
        "continuous_generators": ["translation"],
        "invariants": ["nonnegative_intensity"],
    })
    assert ir.continuous_generators == ("translation",)


def test_all_ten_fronts_are_registered():
    assert len(front_registry()) == 10
