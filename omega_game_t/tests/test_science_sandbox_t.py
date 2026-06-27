import pytest

from omega_game.engines import (
    MicrogridParams,
    MicrogridState,
    RLCParams,
    RLCState,
    ScienceSandboxEngine,
)


def test_rlc_step_updates_time_and_records_oak_memory():
    sandbox = ScienceSandboxEngine()

    result = sandbox.step_rlc(
        state=RLCState(q_coulomb=0.0, i_ampere=0.0),
        params=RLCParams(
            resistance_ohm=10.0,
            inductance_henry=0.1,
            capacitance_farad=0.001,
            source_voltage_volt=5.0,
        ),
        dt_second=0.001,
    )

    assert result.state.t_second == pytest.approx(0.001)
    assert result.state.i_ampere > 0
    assert result.capacitor_energy_joule >= 0
    assert result.inductor_energy_joule >= 0
    assert sandbox.world.memory[-1]["type"] == "rlc_step"
    assert sandbox.gm.m_plus.entries


def test_rlc_params_reject_invalid_values():
    sandbox = ScienceSandboxEngine()

    with pytest.raises(ValueError):
        sandbox.step_rlc(
            state=RLCState(),
            params=RLCParams(
                resistance_ohm=-1.0,
                inductance_henry=0.1,
                capacitance_farad=0.001,
            ),
            dt_second=0.001,
        )


def test_microgrid_serves_load_and_bounds_battery():
    sandbox = ScienceSandboxEngine()

    result = sandbox.step_microgrid(
        state=MicrogridState(battery_energy_wh=250.0),
        params=MicrogridParams(
            battery_capacity_wh=1000.0,
            roundtrip_efficiency=0.9,
            max_charge_power_w=400.0,
            max_discharge_power_w=400.0,
        ),
        solar_power_w=300.0,
        load_power_w=500.0,
        dt_hour=0.25,
    )

    assert 0 <= result.state.battery_energy_wh <= 1000.0
    assert result.served_load_wh > 0
    assert result.unmet_load_wh >= 0
    assert result.loss_wh >= 0
    assert sandbox.world.memory[-1]["type"] == "microgrid_step"


def test_microgrid_charges_from_surplus_solar():
    sandbox = ScienceSandboxEngine()

    result = sandbox.step_microgrid(
        state=MicrogridState(battery_energy_wh=100.0),
        params=MicrogridParams(battery_capacity_wh=1000.0),
        solar_power_w=1000.0,
        load_power_w=100.0,
        dt_hour=0.5,
    )

    assert result.state.battery_energy_wh > 100.0
    assert result.curtailed_solar_wh >= 0


def test_science_sandbox_gm_tick_generates_valid_oak_quest():
    sandbox = ScienceSandboxEngine()
    proposal = sandbox.tick_gm()

    assert proposal.oak_report is not None
    assert proposal.oak_report.accepted
    assert proposal.quest["quest"]
