"""Ω-SPACE-HG-T∞ R0.2 orbital perturbation and attitude OAKBench."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import radians
from typing import Any, Callable

from .attitude import (
    AttitudeControlConfig,
    AttitudeState,
    GyroModel,
    StarTrackerModel,
    quaternion_from_axis_angle,
    quaternion_norm,
    simulate_attitude_control,
)
from .models import OrbitState
from .oak import EARTH_MU_M3_S2, EARTH_RADIUS_M
from .orbit import orbital_period_s, relative_energy_drift
from .perturbations import (
    PerturbationConfig,
    j2_secular_raan_rate_rad_s,
    keplerian_to_cartesian,
    osculating_elements,
    propagate_perturbed,
    unwrap_angle_delta,
)


EARTH_J2 = 1.08262668e-3
EARTH_ROTATION_RAD_S = 7.2921150e-5


@dataclass(frozen=True)
class R02Check:
    name: str
    passed: bool
    observed: Any
    criterion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_perturbation_config(
    *,
    mass_kg: float = 10.0,
    include_drag: bool = False,
    include_srp: bool = False,
) -> PerturbationConfig:
    return PerturbationConfig(
        mu_m3_s2=EARTH_MU_M3_S2,
        body_radius_m=EARTH_RADIUS_M,
        j2=EARTH_J2,
        body_rotation_rad_s=EARTH_ROTATION_RAD_S,
        drag_coefficient=2.2 if include_drag else 0.0,
        drag_area_m2=0.12 if include_drag else 0.0,
        mass_kg=mass_kg,
        reference_density_kg_m3=1.0e-13 if include_drag else 0.0,
        reference_altitude_m=550_000.0,
        density_scale_height_m=65_000.0,
        solar_pressure_n_m2=4.56e-6 if include_srp else 0.0,
        reflectivity_coefficient=1.3 if include_srp else 0.0,
        solar_area_m2=0.12 if include_srp else 0.0,
        sun_direction_inertial=(1.0, 0.0, 0.0),
    )


def canonical_inclined_orbit() -> OrbitState:
    return keplerian_to_cartesian(
        semimajor_axis_m=EARTH_RADIUS_M + 550_000.0,
        eccentricity=0.001,
        inclination_rad=radians(97.6),
        raan_rad=radians(17.0),
        argument_of_periapsis_rad=radians(11.0),
        true_anomaly_rad=radians(5.0),
        mu_m3_s2=EARTH_MU_M3_S2,
    )


def canonical_attitude_case() -> tuple[AttitudeState, tuple[float, float, float, float], AttitudeControlConfig]:
    initial = AttitudeState(
        quaternion_body_to_inertial=quaternion_from_axis_angle((0.0, 1.0, 0.0), radians(35.0)),
        angular_velocity_rad_s=(radians(0.2), radians(-0.1), radians(0.15)),
    )
    target = (1.0, 0.0, 0.0, 0.0)
    controller = AttitudeControlConfig(
        inertia_kg_m2=(0.08, 0.09, 0.05),
        kp_n_m_per_quaternion=(0.008, 0.008, 0.006),
        kd_n_m_s=(0.04, 0.04, 0.03),
        max_wheel_torque_n_m=(0.004, 0.004, 0.003),
        max_wheel_momentum_nms=(0.5, 0.5, 0.4),
        wheel_friction_per_s=0.0,
    )
    return initial, target, controller


def simulate_r02_orbit(
    *,
    duration_orbits: float = 10.0,
    step_s: float = 20.0,
    include_drag: bool = False,
    include_srp: bool = False,
) -> dict[str, Any]:
    initial = canonical_inclined_orbit()
    config = canonical_perturbation_config(include_drag=include_drag, include_srp=include_srp)
    period_s = orbital_period_s(initial, EARTH_MU_M3_S2)
    duration_s = duration_orbits * period_s
    states = propagate_perturbed(initial, duration_s, step_s, config)
    initial_elements = osculating_elements(states[0], EARTH_MU_M3_S2)
    final_elements = osculating_elements(states[-1], EARTH_MU_M3_S2)
    numerical_raan_rate = unwrap_angle_delta(final_elements.raan_rad, initial_elements.raan_rad) / duration_s
    analytical_raan_rate = j2_secular_raan_rate_rad_s(
        initial_elements.semimajor_axis_m,
        initial_elements.eccentricity,
        initial_elements.inclination_rad,
        config,
    )
    relative_raan_error = abs(numerical_raan_rate - analytical_raan_rate) / max(abs(analytical_raan_rate), 1e-30)
    return {
        "model": "J2+optional-exponential-drag+optional-SRP",
        "duration_s": duration_s,
        "step_s": step_s,
        "state_count": len(states),
        "initial_elements": initial_elements.to_dict(),
        "final_elements": final_elements.to_dict(),
        "numerical_raan_rate_rad_s": numerical_raan_rate,
        "analytical_raan_rate_rad_s": analytical_raan_rate,
        "relative_raan_rate_error": relative_raan_error,
        "specific_energy_drift_fraction": relative_energy_drift(states, EARTH_MU_M3_S2),
        "configuration": config.to_dict(),
        "operational_ephemeris_claimed": False,
        "conjunction_assessment_claimed": False,
        "flight_qualified_claimed": False,
    }


def simulate_r02_attitude(
    *,
    duration_s: float = 120.0,
    step_s: float = 0.2,
    sensor_noise: bool = True,
) -> dict[str, Any]:
    initial, target, controller = canonical_attitude_case()
    gyro = GyroModel(
        bias_rad_s=(2.0e-5, -1.5e-5, 1.0e-5) if sensor_noise else (0.0, 0.0, 0.0),
        noise_std_rad_s=8.0e-6 if sensor_noise else 0.0,
        seed=2026,
    )
    tracker = StarTrackerModel(
        noise_std_rad=2.5e-5 if sensor_noise else 0.0,
        seed=2027,
        cadence_steps=5,
    )
    result = simulate_attitude_control(
        initial,
        target,
        duration_s,
        step_s,
        controller,
        gyro=gyro,
        star_tracker=tracker,
        disturbance_torque_n_m=(2.0e-7, -1.0e-7, 1.5e-7),
    )
    payload = result.to_dict(include_states=False)
    payload["configuration"] = {
        "controller": asdict(controller),
        "gyro": asdict(gyro),
        "star_tracker": asdict(tracker),
    }
    payload["flight_software_claimed"] = False
    payload["stability_proof_claimed"] = False
    return payload


def _capture(name: str, criterion: str, function: Callable[[], tuple[bool, Any]]) -> R02Check:
    try:
        passed, observed = function()
        return R02Check(name, bool(passed), observed, criterion)
    except Exception as error:
        return R02Check(name, False, f"{type(error).__name__}: {error}", criterion)


def run_r02_oak_benchmarks() -> dict[str, Any]:
    def j2_check() -> tuple[bool, Any]:
        report = simulate_r02_orbit(duration_orbits=10.0, step_s=20.0)
        error = report["relative_raan_rate_error"]
        return error < 0.02, {
            "relative_raan_rate_error": error,
            "numerical_raan_rate_rad_s": report["numerical_raan_rate_rad_s"],
            "analytical_raan_rate_rad_s": report["analytical_raan_rate_rad_s"],
        }

    def orbit_replay_check() -> tuple[bool, Any]:
        first = simulate_r02_orbit(duration_orbits=1.0, step_s=30.0)
        second = simulate_r02_orbit(duration_orbits=1.0, step_s=30.0)
        keys = ("relative_raan_rate_error", "specific_energy_drift_fraction", "final_elements")
        observed = {key: first[key] for key in keys}
        return all(first[key] == second[key] for key in keys), observed

    def attitude_convergence_check() -> tuple[bool, Any]:
        report = simulate_r02_attitude()
        metrics = report["metrics"]
        passed = (
            metrics["final_error_rad"] < radians(0.5)
            and metrics["final_error_rad"] < 0.02 * metrics["initial_error_rad"]
            and metrics["quaternion_norm_error"] < 1e-12
            and metrics["wheel_saturation_count"] == 0
        )
        return passed, metrics

    def sensor_replay_check() -> tuple[bool, Any]:
        first = simulate_r02_attitude()
        second = simulate_r02_attitude()
        digest = first["deterministic_sensor_digest"]
        return digest == second["deterministic_sensor_digest"], digest

    def quaternion_check() -> tuple[bool, Any]:
        initial, target, controller = canonical_attitude_case()
        result = simulate_attitude_control(initial, target, 30.0, 0.1, controller)
        norms = [quaternion_norm(state.quaternion_body_to_inertial) for state in result.states]
        maximum_error = max(abs(value - 1.0) for value in norms)
        return maximum_error < 1e-12, maximum_error

    def claim_boundary_check() -> tuple[bool, Any]:
        boundaries = {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "flight_qualified_claimed": False,
            "operational_ephemeris_claimed": False,
            "conjunction_assessment_claimed": False,
            "stability_proof_claimed": False,
        }
        return not any(boundaries.values()), boundaries

    checks = (
        _capture("j2_raan_cross_check", "numerical secular RAAN rate within 2% of first-order J2 theory", j2_check),
        _capture("perturbed_orbit_replay", "identical configuration reproduces selected orbital metrics exactly", orbit_replay_check),
        _capture("attitude_closed_loop_convergence", "error < 0.5 deg, >98% reduction, normalized quaternion, no wheel saturation", attitude_convergence_check),
        _capture("deterministic_sensor_replay", "gyro and star-tracker digest replays exactly", sensor_replay_check),
        _capture("quaternion_manifold", "maximum quaternion norm error < 1e-12", quaternion_check),
        _capture("r02_claim_boundaries", "no theorem, validation, flight or operational claim", claim_boundary_check),
    )
    return {
        "suite": "OMEGA-SPACE-HG-T-R0.2-OAKBench",
        "passed": all(check.passed for check in checks),
        "checks": [check.to_dict() for check in checks],
        "theorem_claimed": False,
        "scientific_validation_claimed": False,
        "flight_qualified_claimed": False,
        "operational_ephemeris_claimed": False,
        "conjunction_assessment_claimed": False,
        "stability_proof_claimed": False,
        "limitations": [
            "first-order J2 only; no validated gravity-field model",
            "exponential drag is an illustrative atmosphere baseline",
            "SRP uses a fixed inertial Sun direction unless replaced by a caller model",
            "principal-axis rigid body and idealized reaction-wheel body torques",
            "deterministic synthetic sensor errors, not calibrated hardware models",
            "no orbit determination, covariance realism, HIL or flight qualification",
        ],
    }
