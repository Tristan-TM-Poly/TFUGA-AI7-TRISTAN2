import pytest

from omega_game.engines import CircuitDoor, CircuitDungeonEngine, RLCParams


def test_circuit_door_resonance_frequency_is_positive():
    door = CircuitDoor(
        door_id="d1",
        name="Door",
        params=RLCParams(resistance_ohm=10.0, inductance_henry=0.1, capacitance_farad=0.001),
    )

    assert door.resonance_frequency_hz > 0
    assert door.accepts_frequency(door.resonance_frequency_hz)


def test_circuit_dungeon_opens_door_near_resonance_and_records_m_plus():
    dungeon = CircuitDungeonEngine.demo_dungeon()
    door = dungeon.doors["door_resonance_1"]

    result = dungeon.attempt_frequency("door_resonance_1", door.resonance_frequency_hz)

    assert result.opened
    assert result.oak_accepted
    assert door.opened
    assert dungeon.world.entities["door_resonance_1"].attributes["opened"] is True
    assert dungeon.gm.m_plus.entries
    assert dungeon.world.memory[-1]["type"] == "circuit_door_opened"


def test_circuit_dungeon_rejects_frequency_outside_tolerance_and_records_m_minus():
    dungeon = CircuitDungeonEngine.demo_dungeon()
    door = dungeon.doors["door_resonance_1"]

    result = dungeon.attempt_frequency("door_resonance_1", door.resonance_frequency_hz * 1.5)

    assert not result.opened
    assert result.oak_accepted
    assert dungeon.gm.m_minus.entries
    assert dungeon.gm.m_minus.last()["reason"] == "frequency_outside_tolerance"
    assert dungeon.world.memory[-1]["type"] == "circuit_door_attempt_failed"


def test_circuit_dungeon_rejects_invalid_frequency():
    dungeon = CircuitDungeonEngine.demo_dungeon()

    with pytest.raises(ValueError):
        dungeon.attempt_frequency("door_resonance_1", 0.0)


def test_circuit_dungeon_validates_door_params():
    with pytest.raises(ValueError):
        CircuitDoor(
            door_id="bad",
            name="Bad Door",
            params=RLCParams(resistance_ohm=1.0, inductance_henry=0.0, capacitance_farad=0.001),
        )


def test_circuit_dungeon_gm_tick_generates_valid_oak_quest():
    dungeon = CircuitDungeonEngine.demo_dungeon()
    proposal = dungeon.tick_gm()

    assert proposal.oak_report is not None
    assert proposal.oak_report.accepted
    assert proposal.quest["quest"]
