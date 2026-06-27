"""CircuitDungeon-T: RLC puzzle layer for Ω-GAME-T.

CircuitDungeon-T turns safe educational circuit models into playable gates.
It is a virtual learning/simulation layer only, not hardware guidance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import pi, sqrt

from ..core import Entity, Event, RuleKernel, WorldGraph
from ..gm import GameMasterAgent, GMProposal
from .science_sandbox import RLCParams, ScienceSandboxEngine


@dataclass(slots=True)
class CircuitDoor:
    """A virtual RLC door opened by a frequency near resonance."""

    door_id: str
    name: str
    params: RLCParams
    tolerance_ratio: float = 0.05
    opened: bool = False

    def __post_init__(self) -> None:
        self.params.validate()
        if not 0 < self.tolerance_ratio <= 1:
            raise ValueError("tolerance_ratio must be in (0, 1].")

    @property
    def resonance_frequency_hz(self) -> float:
        return 1.0 / (2.0 * pi * sqrt(self.params.inductance_henry * self.params.capacitance_farad))

    def accepts_frequency(self, frequency_hz: float) -> bool:
        if frequency_hz <= 0:
            return False
        tolerance_hz = self.resonance_frequency_hz * self.tolerance_ratio
        return abs(frequency_hz - self.resonance_frequency_hz) <= tolerance_hz


@dataclass(slots=True)
class CircuitAttemptResult:
    door_id: str
    frequency_hz: float
    target_frequency_hz: float
    error_ratio: float
    opened: bool
    oak_accepted: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CircuitDungeonEngine:
    """Virtual dungeon where RLC resonance opens doors."""

    world: WorldGraph = field(default_factory=WorldGraph)
    gm: GameMasterAgent = field(default_factory=GameMasterAgent)
    rule_kernel: RuleKernel = field(default_factory=RuleKernel)
    sandbox: ScienceSandboxEngine | None = None
    doors: dict[str, CircuitDoor] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sandbox is None:
            self.sandbox = ScienceSandboxEngine(world=self.world, gm=self.gm, rule_kernel=self.rule_kernel)
        if "circuit_dungeon" not in self.world.entities:
            self.world.add_entity(
                Entity(
                    entity_id="circuit_dungeon",
                    kind="location",
                    name="CircuitDungeon-T",
                    attributes={"oak_mode": "educational_virtual_circuits", "power": 0.5},
                )
            )

    def add_player(self, player_id: str = "player_tristan", name: str = "Tristan") -> None:
        if player_id not in self.world.entities:
            self.world.add_entity(
                Entity(
                    entity_id=player_id,
                    kind="player",
                    name=name,
                    attributes={"power": 0.5, "style": "circuit-reasoner"},
                )
            )
        self.world.add_relation(player_id, "enters", "circuit_dungeon")

    def add_door(self, door: CircuitDoor) -> None:
        if door.door_id in self.doors:
            raise ValueError(f"Door already exists: {door.door_id}")
        self.doors[door.door_id] = door
        self.world.add_entity(
            Entity(
                entity_id=door.door_id,
                kind="circuit_door",
                name=door.name,
                attributes={
                    "resistance_ohm": door.params.resistance_ohm,
                    "inductance_henry": door.params.inductance_henry,
                    "capacitance_farad": door.params.capacitance_farad,
                    "resonance_frequency_hz": door.resonance_frequency_hz,
                    "tolerance_ratio": door.tolerance_ratio,
                    "opened": door.opened,
                    "power": 0.5,
                },
            )
        )
        self.world.add_relation("circuit_dungeon", "contains", door.door_id)

    def attempt_frequency(
        self,
        door_id: str,
        frequency_hz: float,
        player_id: str = "player_tristan",
    ) -> CircuitAttemptResult:
        if door_id not in self.doors:
            raise KeyError(f"Unknown circuit door: {door_id}")
        if frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive.")
        if player_id not in self.world.entities:
            self.add_player(player_id)

        door = self.doors[door_id]
        target = door.resonance_frequency_hz
        error_ratio = abs(frequency_hz - target) / target
        opened = door.accepts_frequency(frequency_hz)

        event = Event(
            event_id=f"circuit_attempt_{door_id}_{len(self.world.memory) + 1}",
            kind="circuit_frequency_attempt",
            description=f"Attempt {frequency_hz:.6g} Hz on {door.name}",
            actors=[player_id],
            targets=[door_id],
            payload={
                "frequency_hz": frequency_hz,
                "target_frequency_hz": target,
                "error_ratio": error_ratio,
                "opened": opened,
                "fair": True,
                "fun": True,
                "agency": 1.0,
                "metric": "frequency_error_ratio",
                "expected_signal": "door opens when proposed frequency is within tolerance",
                "risk_flags": [],
            },
        )
        report = self.gm.oak_gate.validate(self.world, event, self.rule_kernel)

        result = CircuitAttemptResult(
            door_id=door_id,
            frequency_hz=frequency_hz,
            target_frequency_hz=target,
            error_ratio=error_ratio,
            opened=opened and report.accepted,
            oak_accepted=report.accepted,
            reasons=report.reasons,
        )
        result_payload = asdict(result)

        if result.opened:
            door.opened = True
            self.world.entities[door_id].attributes["opened"] = True
            self.world.remember(
                {
                    "type": "circuit_door_opened",
                    "door_id": door_id,
                    "frequency_hz": frequency_hz,
                    "target_frequency_hz": target,
                    "error_ratio": error_ratio,
                    "oak": report.metrics,
                }
            )
            self.gm.m_plus.record("circuit_door_opened", result_payload)
        else:
            reason = "frequency_outside_tolerance" if report.accepted else "oak_rejected_circuit_attempt"
            self.gm.m_minus.record(reason, result_payload)
            self.world.remember(
                {
                    "type": "circuit_door_attempt_failed",
                    "door_id": door_id,
                    "frequency_hz": frequency_hz,
                    "target_frequency_hz": target,
                    "error_ratio": error_ratio,
                    "oak_accepted": report.accepted,
                    "reasons": report.reasons,
                }
            )
        return result

    def tick_gm(self) -> GMProposal:
        return self.gm.step(self.world, self.rule_kernel)

    @classmethod
    def demo_dungeon(cls) -> "CircuitDungeonEngine":
        dungeon = cls()
        dungeon.add_player()
        dungeon.add_door(
            CircuitDoor(
                door_id="door_resonance_1",
                name="Porte de résonance RLC-1",
                params=RLCParams(
                    resistance_ohm=10.0,
                    inductance_henry=0.1,
                    capacitance_farad=0.001,
                    source_voltage_volt=5.0,
                ),
                tolerance_ratio=0.05,
            )
        )
        return dungeon


__all__ = ["CircuitAttemptResult", "CircuitDoor", "CircuitDungeonEngine"]
