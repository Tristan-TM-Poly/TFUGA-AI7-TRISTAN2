"""Generative taxonomy for satellites, vehicles, modules and mission regimes."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


MISSION_CLASSES = (
    "earth_observation_optical",
    "earth_observation_hyperspectral",
    "earth_observation_thermal",
    "synthetic_aperture_radar",
    "meteorology",
    "climate_monitoring",
    "communications_broadband",
    "communications_direct_to_device",
    "navigation_positioning_timing",
    "technology_demonstration",
    "astronomy_observatory",
    "heliophysics",
    "magnetosphere_ionosphere",
    "geodesy_gravimetry",
    "space_weather",
    "formation_interferometry",
    "on_orbit_servicing",
    "inspection_and_rendezvous",
    "orbital_logistics",
    "in_space_manufacturing",
    "cislunar_relay",
    "lunar_orbiter",
    "lunar_surface_science",
    "planetary_orbiter",
    "planetary_lander",
    "planetary_rover",
    "atmospheric_probe",
    "sample_return",
    "small_body_reconnaissance",
    "deep_space_probe",
    "educational_cubesat",
)

VEHICLE_AND_MODULE_CLASSES = (
    "picosatellite",
    "nanosatellite",
    "cubesat_1u_3u_6u_12u_27u",
    "smallsat_bus",
    "medium_satellite_bus",
    "large_satellite_bus",
    "hosted_payload_platform",
    "fractionated_spacecraft",
    "distributed_spacecraft_swarm",
    "formation_flying_element",
    "communications_relay",
    "navigation_beacon",
    "space_telescope",
    "radar_platform",
    "orbital_tug",
    "servicing_vehicle",
    "inspection_vehicle",
    "propulsion_module",
    "service_module",
    "power_module",
    "thermal_module",
    "communications_module",
    "avionics_module",
    "payload_module",
    "pressurized_habitat",
    "laboratory_module",
    "airlock_module",
    "logistics_module",
    "life_support_module",
    "emergency_refuge_module",
    "lander",
    "ascent_vehicle",
    "rover",
    "hopper",
    "surface_power_station",
    "surface_communications_station",
    "sample_cache",
    "return_capsule",
    "solar_sail",
    "drag_sail",
)

ENVIRONMENT_CLASSES = (
    "suborbital",
    "very_low_earth_orbit",
    "low_earth_orbit",
    "sun_synchronous_orbit",
    "medium_earth_orbit",
    "highly_elliptical_orbit",
    "geostationary_orbit",
    "earth_moon_lagrange",
    "cislunar_orbit",
    "lunar_orbit",
    "lunar_surface",
    "mars_orbit",
    "mars_surface",
    "planetary_atmosphere",
    "small_body_proximity",
    "heliocentric_orbit",
    "solar_proximity",
    "deep_space",
)

SUBSYSTEM_CLASSES = (
    "mission_and_payload",
    "structures_and_mechanisms",
    "guidance_navigation_control",
    "electrical_power",
    "thermal_control",
    "radio_frequency_communications",
    "optical_communications",
    "command_and_data_handling",
    "flight_software",
    "onboard_autonomy",
    "chemical_propulsion",
    "electric_propulsion",
    "propellantless_mobility",
    "radiation_assurance",
    "reliability_fdir",
    "cybersecurity_command_integrity",
    "human_systems_life_support",
    "robotics_and_docking",
    "ground_segment",
    "mission_operations",
    "launch_and_deployment",
    "end_of_life_passivation_disposal",
)

SIMULATION_DOMAINS = (
    "requirements_traceability",
    "orbital_dynamics",
    "attitude_dynamics",
    "sensor_estimation",
    "control_and_actuation",
    "structural_modes",
    "launch_loads",
    "mechanism_deployment",
    "electrical_power",
    "battery_aging",
    "thermal_network",
    "communications_link_budget",
    "network_routing",
    "onboard_data_flow",
    "radiation_environment",
    "reliability_fault_trees",
    "software_in_the_loop",
    "processor_in_the_loop",
    "hardware_in_the_loop",
    "constellation_coverage",
    "conjunction_and_debris_risk",
    "ground_operations",
    "lifecycle_cost",
    "manufacturing_and_integration",
)

FIDELITY_LEVELS = (
    "L0_symbolic_budget",
    "L1_reduced_order_deterministic",
    "L2_coupled_time_domain",
    "L3_monte_carlo_uncertainty",
    "L4_external_tool_crosscheck",
    "L5_software_processor_hardware_loop",
    "L6_environmental_qualification_evidence",
    "L7_flight_data_calibration",
)


def atlas_manifest() -> dict[str, Any]:
    payload = {
        "atlas": "OMEGA-SPACE-HG-T-INFINITY-R0.1",
        "mission_classes": list(MISSION_CLASSES),
        "vehicle_and_module_classes": list(VEHICLE_AND_MODULE_CLASSES),
        "environment_classes": list(ENVIRONMENT_CLASSES),
        "subsystem_classes": list(SUBSYSTEM_CLASSES),
        "simulation_domains": list(SIMULATION_DOMAINS),
        "fidelity_levels": list(FIDELITY_LEVELS),
        "counts": {
            "mission_classes": len(MISSION_CLASSES),
            "vehicle_and_module_classes": len(VEHICLE_AND_MODULE_CLASSES),
            "environment_classes": len(ENVIRONMENT_CLASSES),
            "subsystem_classes": len(SUBSYSTEM_CLASSES),
            "simulation_domains": len(SIMULATION_DOMAINS),
            "fidelity_levels": len(FIDELITY_LEVELS),
            "cross_reference_cells": len(MISSION_CLASSES)
            * len(VEHICLE_AND_MODULE_CLASSES)
            * len(ENVIRONMENT_CLASSES)
            * len(SUBSYSTEM_CLASSES)
            * len(SIMULATION_DOMAINS)
            * len(FIDELITY_LEVELS),
        },
        "permanent_generated_architecture_cap": None,
        "claim_boundary": (
            "taxonomy and addressable combinations are not executed simulations, "
            "feasible spacecraft, certified designs or flight evidence"
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def select_atlas_slice(
    *,
    missions: tuple[str, ...] = (),
    modules: tuple[str, ...] = (),
    environments: tuple[str, ...] = (),
) -> dict[str, Any]:
    selected_missions = missions or MISSION_CLASSES
    selected_modules = modules or VEHICLE_AND_MODULE_CLASSES
    selected_environments = environments or ENVIRONMENT_CLASSES
    unknown = {
        "missions": sorted(set(selected_missions) - set(MISSION_CLASSES)),
        "modules": sorted(set(selected_modules) - set(VEHICLE_AND_MODULE_CLASSES)),
        "environments": sorted(set(selected_environments) - set(ENVIRONMENT_CLASSES)),
    }
    if any(unknown.values()):
        raise ValueError(f"unknown atlas values: {unknown}")
    return {
        "missions": list(selected_missions),
        "modules": list(selected_modules),
        "environments": list(selected_environments),
        "candidate_triplets": len(selected_missions) * len(selected_modules) * len(selected_environments),
        "executed_simulations": 0,
        "flight_qualified_claimed": False,
    }
