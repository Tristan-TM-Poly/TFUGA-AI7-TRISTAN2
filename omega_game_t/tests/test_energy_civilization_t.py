import pytest

from omega_game.engines import (
    EnergyCivilizationEngine,
    EnergyColony,
    EnergyTurnInput,
    MicrogridParams,
    MicrogridState,
)


def test_energy_civilization_served_turn_records_m_plus():
    engine = EnergyCivilizationEngine.demo_civilization()

    result = engine.play_turn(
        "colony_solar_1",
        EnergyTurnInput(solar_power_w=800.0, load_power_w=300.0, dt_hour=0.5),
    )

    assert result.oak_accepted
    assert result.service_ratio == pytest.approx(1.0)
    assert result.energy_score > 0.8
    assert engine.gm.m_plus.entries
    assert engine.world.memory[-1]["type"] == "energy_turn"


def test_energy_civilization_stressed_turn_records_m_minus_when_unserved():
    engine = EnergyCivilizationEngine.demo_civilization()

    result = engine.play_turn(
        "colony_solar_1",
        EnergyTurnInput(solar_power_w=0.0, load_power_w=2000.0, dt_hour=1.0),
    )

    assert result.oak_accepted
    assert result.service_ratio < 1.0
    assert result.unmet_load_wh > 0
    assert engine.gm.m_minus.entries


def test_energy_civilization_keeps_battery_bounded():
    engine = EnergyCivilizationEngine.demo_civilization()

    for _ in range(5):
        result = engine.play_turn(
            "colony_solar_1",
            EnergyTurnInput(solar_power_w=2000.0, load_power_w=50.0, dt_hour=1.0),
        )

    assert 0 <= result.battery_energy_wh <= 1000.0


def test_energy_colony_rejects_invalid_initial_battery():
    with pytest.raises(ValueError):
        EnergyColony(
            colony_id="bad",
            name="Bad",
            state=MicrogridState(battery_energy_wh=2000.0),
            params=MicrogridParams(battery_capacity_wh=1000.0),
        )


def test_energy_turn_input_rejects_negative_values():
    turn = EnergyTurnInput(solar_power_w=-1.0, load_power_w=1.0, dt_hour=1.0)

    with pytest.raises(ValueError):
        turn.validate()


def test_energy_civilization_gm_tick_generates_valid_oak_quest():
    engine = EnergyCivilizationEngine.demo_civilization()
    proposal = engine.tick_gm()

    assert proposal.oak_report is not None
    assert proposal.oak_report.accepted
    assert proposal.quest["quest"]
