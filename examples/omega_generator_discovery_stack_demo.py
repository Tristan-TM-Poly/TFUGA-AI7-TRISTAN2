"""Demonstrate every Ω-GENERATOR-DISCOVERY-STACK front."""
from __future__ import annotations

import json
from math import cos, pi, sin

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


def main() -> None:
    axis = [index * 0.1 for index in range(-100, 101)]
    before = lorentzian(axis, area=1.0, center=0.0, hwhm=0.5)
    after = lorentzian(axis, area=1.2, center=0.8, hwhm=0.7)
    scalar = fit_scalar_generator([1, 3, 7, 15])

    result = {
        "fronts": [front.to_dict() for front in front_registry()],
        "affine": identify_affine_1d([0, 1, 2], [2, 5, 8]).to_dict(),
        "generator_operator": {
            "multiplier": scalar.multiplier,
            "forcing": scalar.forcing,
            "continuous_rate": scalar.continuous_rate,
            "residual": scalar.residual,
        },
        "semigroup_defect": semigroup_defect(
            ((2.0, 0.0), (0.0, 0.5)),
            ((4.0, 0.0), (0.0, 0.25)),
        ),
        "spectral": compare_spectra(axis, before, after).to_dict(),
        "holonomy": crystal_holonomy([
            (1.0, 0.0, 0.0, 0.0),
            (cos(pi/8), 0.0, 0.0, sin(pi/8)),
            (cos(pi/4), 0.0, 0.0, sin(pi/4)),
        ]).to_dict(),
        "order": design_order_experiment(
            ((1.0, 1.0), (0.0, 1.0)),
            ((1.0, 0.0), (1.0, 1.0)),
        ).to_dict(),
        "morph_ir": compile_morph_ir({
            "name": "raman_temperature_step",
            "domain": "spectrum",
            "codomain": "spectrum",
            "continuous_generators": ["shift", "broadening", "amplitude"],
            "discrete_events": ["phase_birth"],
            "invariants": ["nonnegative_intensity"],
            "residual": 0.02,
            "uncertainty": 0.01,
        }).to_dict(),
        "epistemic": evidence_growth_transition(
            concepts_before=100,
            concepts_after=140,
            evidence_before=25,
            evidence_after=30,
        ).to_dict(),
        "autolab": [
            item.to_dict()
            for item in prioritize_experiments([
                ExperimentCandidate("low_power_raman_scan", 0.5, 0.8, 0.7, 0.1, 0.05, True),
                ExperimentCandidate("irreversible_high_heat", 0.9, 0.9, 0.8, 0.5, 0.4, False),
            ])
        ],
        "protocol": compile_protocol({
            "instrument_id": "raman_001",
            "inputs": ["laser_power", "integration_time"],
            "outputs": ["spectrum", "temperature"],
            "generators": ["acquisition", "calibration"],
            "safety_limits": {"laser_power": 10.0, "temperature": 350.0},
            "rollback_steps": ["restore_previous_settings", "disable_laser"],
        }).to_dict(),
        "syndrome": generator_syndrome(
            ((1.0, 0.0), (0.0, 1.0)),
            ((1.01, 0.0), (0.0, 1.0)),
        ).to_dict(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
