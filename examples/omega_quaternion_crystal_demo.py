"""Executable Ω-QUATERNION-CRYSTAL-T demonstration.

The numbers are dimensionless demonstration values. A real material study must
attach units, provenance, temperature, constitutive assumptions, and boundary
conditions before interpreting the output physically.
"""

from __future__ import annotations

import json

from omega_quaternion_crystal_t import (
    AffineTransform3D,
    CrystalState,
    CubicElasticity,
    Quaternion,
    elastic_energy_density,
    hooke_stress,
    radians,
    resolved_shear_stress,
)


def main() -> None:
    orientation = Quaternion.from_axis_angle((1.0, 1.0, 0.0), radians(35.0))
    stretch = (
        (1.015, 0.008, 0.0),
        (0.008, 0.992, 0.004),
        (0.0, 0.004, 0.998),
    )
    crystal_map = AffineTransform3D.crystal_map(
        orientation,
        stretch,
        translation=(0.2, -0.1, 0.05),
    )

    elasticity = CubicElasticity(c11=200.0, c12=120.0, c44=80.0)
    strain_crystal = (
        (0.010, 0.002, 0.000),
        (0.002, -0.003, 0.001),
        (0.000, 0.001, 0.001),
    )
    stress_crystal = hooke_stress(elasticity.to_tensor(), strain_crystal)
    state = CrystalState(
        orientation=orientation,
        deformation_gradient=crystal_map.linear,
        stress_crystal=stress_crystal,
    )

    slip_direction_crystal = (1.0, 0.0, 0.0)
    plane_normal_crystal = (0.0, 1.0, 0.0)
    slip_direction_lab = orientation.rotate_vector(slip_direction_crystal)
    plane_normal_lab = orientation.rotate_vector(plane_normal_crystal)
    tau = resolved_shear_stress(
        state.stress_lab,
        slip_direction_lab,
        plane_normal_lab,
    )

    output = {
        "status": "prototype",
        "orientation_quaternion": {
            "w": orientation.w,
            "x": orientation.x,
            "y": orientation.y,
            "z": orientation.z,
        },
        "mapped_probe_point": crystal_map.apply((1.0, 0.0, 0.0)),
        "elasticity_stable": elasticity.is_mechanically_stable(),
        "stability_margins": elasticity.stability_margins(),
        "strain_crystal": strain_crystal,
        "stress_crystal": stress_crystal,
        "stress_lab": state.stress_lab,
        "elastic_energy_density": elastic_energy_density(stress_crystal, strain_crystal),
        "resolved_shear_stress": tau,
        "oak_invariants": state.invariants(),
        "limits": [
            "dimensionless demonstration constants",
            "small-strain linear cubic elasticity",
            "no plastic flow rule or damage model",
            "no thermal, electrical, magnetic, optical, or chemical coupling yet",
        ],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
