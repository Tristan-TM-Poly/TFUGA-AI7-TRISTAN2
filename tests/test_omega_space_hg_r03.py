from __future__ import annotations

import pytest

from omega_space_hg_t.networks import (
    BatteryConfig,
    DataQueueConfig,
    DataQueueState,
    LinkBudgetConfig,
    ThermalConductance,
    ThermalNetwork,
    ThermalNodeConfig,
    data_queue_step,
    initial_battery_state,
    link_budget,
    power_step,
)
from omega_space_hg_t.r02 import canonical_inclined_orbit
from omega_space_hg_t.r03 import (
    cylindrical_illumination,
    run_r03_oak_benchmarks,
    simulate_r03_networks,
)


def test_closed_thermal_network_conserves_total_energy() -> None:
    network = ThermalNetwork(
        (
            ThermalNodeConfig("hot", 1000.0, 320.0),
            ThermalNodeConfig("cold", 2000.0, 280.0),
        ),
        (ThermalConductance("hot", "cold", 5.0),),
    )
    state = network.initial_state()
    initial_energy = 1000.0 * 320.0 + 2000.0 * 280.0
    for _ in range(100):
        report = network.step(state, 0.2)
        state = report.state
        assert abs(report.energy_balance_residual_j) < 1e-8
    final_energy = 1000.0 * state.temperatures_k["hot"] + 2000.0 * state.temperatures_k["cold"]
    assert final_energy == pytest.approx(initial_energy, abs=1e-8)


def test_thermal_network_rejects_unknown_conductance_nodes() -> None:
    with pytest.raises(ValueError):
        ThermalNetwork(
            (ThermalNodeConfig("known", 1000.0, 300.0),),
            (ThermalConductance("known", "missing", 1.0),),
        )


def test_battery_step_enforces_soc_and_current_limits() -> None:
    config = BatteryConfig(
        capacity_wh=100.0,
        initial_soc=0.5,
        nominal_voltage_v=10.0,
        internal_resistance_ohm=0.1,
        maximum_charge_current_a=2.0,
        maximum_discharge_current_a=2.0,
        minimum_soc=0.2,
        maximum_soc=0.9,
    )
    state = initial_battery_state(config)
    charged = power_step(state, config, 3600.0, generated_power_w=1000.0, requested_load_w=0.0)
    discharged = power_step(charged.state, config, 3600.0, generated_power_w=0.0, requested_load_w=1000.0)
    assert charged.state.soc(config) <= config.maximum_soc
    assert discharged.state.soc(config) >= config.minimum_soc
    assert abs(charged.battery_current_a) <= config.maximum_charge_current_a
    assert abs(discharged.battery_current_a) <= config.maximum_discharge_current_a
    assert discharged.unmet_load_w > 0.0


def test_free_space_path_loss_obeys_inverse_square_scaling() -> None:
    def budget(distance: float):
        return link_budget(
            LinkBudgetConfig(
                frequency_hz=2.2e9,
                distance_m=distance,
                transmit_power_w=5.0,
                transmit_gain_dbi=3.0,
                receive_gain_dbi=30.0,
                system_losses_db=2.0,
                system_noise_temperature_k=400.0,
                bandwidth_hz=1e6,
            )
        )

    near = budget(1e6)
    far = budget(2e6)
    assert far.free_space_path_loss_db - near.free_space_path_loss_db == pytest.approx(
        6.020599913279624,
        abs=1e-12,
    )
    assert far.received_power_dbw < near.received_power_dbw


def test_data_queue_accounts_for_delivery_and_overflow() -> None:
    config = DataQueueConfig(capacity_bits=1000.0)
    state = data_queue_step(
        DataQueueState(),
        config,
        1.0,
        generated_bps=800.0,
        downlink_bps=300.0,
    )
    assert state.stored_bits == pytest.approx(500.0)
    assert state.delivered_bits == pytest.approx(300.0)
    state = data_queue_step(
        state,
        config,
        1.0,
        generated_bps=1000.0,
        downlink_bps=0.0,
    )
    assert state.stored_bits == pytest.approx(1000.0)
    assert state.dropped_bits == pytest.approx(500.0)


def test_ground_contact_windows_are_replayable() -> None:
    report_a = simulate_r03_networks(duration_orbits=8.0, step_s=20.0)
    report_b = simulate_r03_networks(duration_orbits=8.0, step_s=20.0)
    assert report_a["communications"] == report_b["communications"]
    assert report_a["communications"]["contact_window_count"] >= 1
    assert report_a["communications"]["total_contact_s_sampled"] > 0.0


def test_cylindrical_eclipse_is_geometrically_consistent() -> None:
    state = canonical_inclined_orbit()
    sunward = type(state)((abs(state.position_m[0]), 0.0, 0.0), state.velocity_m_s, state.epoch_s)
    anti_sunward = type(state)((-abs(state.position_m[0]), 0.0, 0.0), state.velocity_m_s, state.epoch_s)
    off_axis = type(state)((-abs(state.position_m[0]), 2.0 * 6_378_137.0, 0.0), state.velocity_m_s, state.epoch_s)
    assert cylindrical_illumination(sunward) is True
    assert cylindrical_illumination(anti_sunward) is False
    assert cylindrical_illumination(off_axis) is True


def test_integrated_r03_network_fixture_is_safe_and_nonoperational() -> None:
    report = simulate_r03_networks(duration_orbits=8.0, step_s=20.0)
    assert report["safe_fixture"] is True
    assert report["power"]["minimum_soc"] > 0.15
    assert report["data"]["dropped_gb"] == 0.0
    assert report["data"]["delivered_gb"] > 0.0
    assert report["data"]["maximum_stored_fraction"] < 0.95
    assert report["operational_network_claimed"] is False
    assert report["regulatory_approval_claimed"] is False


def test_r03_oakbench_passes_reduced_network_fixtures_only() -> None:
    report = run_r03_oak_benchmarks()
    assert report["passed"] is True
    assert len(report["checks"]) >= 6
    assert report["theorem_claimed"] is False
    assert report["flight_qualified_claimed"] is False
    assert report["operational_network_claimed"] is False
    assert report["regulatory_approval_claimed"] is False
