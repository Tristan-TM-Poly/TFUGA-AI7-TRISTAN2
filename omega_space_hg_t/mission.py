"""Mission compilation and coupled simulation for Ω-SPACE-HG-T∞."""
from __future__ import annotations

from typing import Any

from .hypergraph import SpaceHyperedge, SpaceNode, build_spacecraft_hypergraph
from .models import MissionConfig, MissionMetrics, MissionResult, SimulationPoint
from .orbit import orbital_period_s, propagate_two_body, relative_energy_drift
from .power_thermal import advance_bus, initial_bus_state


DEFAULT_SUBSYSTEMS = (
    "payload",
    "structure",
    "guidance_navigation_control",
    "electrical_power",
    "thermal_control",
    "communications",
    "command_data_handling",
    "flight_software",
    "propulsion",
    "fault_detection_isolation_recovery",
    "radiation_reliability",
    "ground_segment",
    "operations",
    "end_of_life",
)


def compile_mission_hypergraph(config: MissionConfig) -> dict[str, Any]:
    requirements = (
        "Maintain positive energy reserve throughout the simulated mission",
        "Keep the reduced thermal node within declared model limits",
        "Avoid storage saturation under the deterministic operations schedule",
        "Preserve traceability from mission objective to subsystem models",
        "Retain explicit non-qualification and non-proof boundaries",
    )
    graph = build_spacecraft_hypergraph(config.mission_id, DEFAULT_SUBSYSTEMS, requirements)
    objective_id = "objective:primary"
    graph.add_node(
        SpaceNode(
            objective_id,
            "objective",
            {"statement": config.objective},
            oak_status="declared",
        )
    )
    graph.add_edge(SpaceHyperedge("mission:objective", "serves", (config.mission_id, objective_id)))

    flows = {
        "energy-flow": ("subsystem:electrical_power", "subsystem:payload", "subsystem:communications"),
        "thermal-flow": ("subsystem:thermal_control", "subsystem:electrical_power", "subsystem:payload"),
        "data-flow": ("subsystem:payload", "subsystem:command_data_handling", "subsystem:communications", "subsystem:ground_segment"),
        "control-loop": ("subsystem:guidance_navigation_control", "subsystem:flight_software", "subsystem:fault_detection_isolation_recovery"),
        "lifecycle": ("subsystem:operations", "subsystem:end_of_life", config.mission_id),
    }
    for edge_id, members in flows.items():
        graph.add_edge(SpaceHyperedge(edge_id, edge_id, members, {"model_level": "R0.1-reduced"}))
    return graph.to_dict()


def simulate_mission(config: MissionConfig) -> MissionResult:
    """Run the transparent R0.1 orbit-power-thermal-data co-simulation."""

    config.validate()
    orbit_states = propagate_two_body(
        config.orbit,
        config.duration_s,
        config.step_s,
        config.central_body_mu_m3_s2,
    )
    period_s = orbital_period_s(config.orbit, config.central_body_mu_m3_s2)
    bus_state = initial_bus_state(config.spacecraft)
    points: list[SimulationPoint] = []

    for index, orbit_state in enumerate(orbit_states):
        if index == 0:
            in_eclipse = False
            generated_power_w = 0.0
            load_power_w = config.spacecraft.base_load_w
        else:
            dt_s = orbit_state.epoch_s - orbit_states[index - 1].epoch_s
            step = advance_bus(
                bus_state,
                config.spacecraft,
                dt_s,
                time_s=orbit_states[index - 1].epoch_s,
                period_s=period_s,
                eclipse_fraction=config.eclipse_fraction,
                payload_duty_cycle=config.payload_duty_cycle,
                downlink_duty_cycle=config.downlink_duty_cycle,
                solar_flux_w_m2=config.solar_flux_w_m2,
                albedo_flux_w_m2=config.albedo_flux_w_m2,
                deep_space_temperature_k=config.deep_space_temperature_k,
            )
            bus_state = step.state
            in_eclipse = step.in_eclipse
            generated_power_w = step.generated_power_w
            load_power_w = step.load_power_w
        points.append(
            SimulationPoint(
                time_s=orbit_state.epoch_s,
                position_m=orbit_state.position_m,
                velocity_m_s=orbit_state.velocity_m_s,
                in_eclipse=in_eclipse,
                generated_power_w=generated_power_w,
                load_power_w=load_power_w,
                battery_wh=bus_state.battery_wh,
                temperature_k=bus_state.temperature_k,
                stored_data_gb=bus_state.stored_data_gb,
            )
        )

    battery_fractions = [point.battery_wh / config.spacecraft.battery_capacity_wh for point in points]
    temperatures = [point.temperature_k for point in points]
    storage_fractions = [point.stored_data_gb / config.spacecraft.storage_capacity_gb for point in points]
    violations: list[str] = []
    if min(battery_fractions) < 0.10:
        violations.append("battery_reserve_below_10_percent")
    if min(temperatures) < 250.0:
        violations.append("temperature_below_reduced_model_limit")
    if max(temperatures) > 330.0:
        violations.append("temperature_above_reduced_model_limit")
    if max(storage_fractions) >= 0.98:
        violations.append("storage_near_saturation")

    metrics = MissionMetrics(
        energy_drift_fraction=relative_energy_drift(orbit_states, config.central_body_mu_m3_s2),
        minimum_battery_fraction=min(battery_fractions),
        maximum_battery_fraction=max(battery_fractions),
        minimum_temperature_k=min(temperatures),
        maximum_temperature_k=max(temperatures),
        maximum_stored_data_fraction=max(storage_fractions),
        completed_fraction=1.0,
        safe=not violations,
        violations=tuple(violations),
    )
    return MissionResult(
        config=config,
        points=tuple(points),
        metrics=metrics,
        hypergraph=compile_mission_hypergraph(config),
    )
