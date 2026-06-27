"""EnergyCivilization-T: microgrid strategy layer for Ω-GAME-T.

This engine turns the educational MicrogridStep model into a turn-based
strategy loop. It is a game/simulation layer, not infrastructure guidance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..core import Entity, Event, RuleKernel, WorldGraph
from ..gm import GameMasterAgent, GMProposal
from .science_sandbox import MicrogridParams, MicrogridState, ScienceSandboxEngine


@dataclass(slots=True)
class EnergyColony:
    colony_id: str
    name: str
    state: MicrogridState
    params: MicrogridParams
    population: int = 100
    stability: float = 1.0

    def __post_init__(self) -> None:
        self.params.validate()
        if self.population < 0:
            raise ValueError("population must be non-negative.")
        if not 0 <= self.stability <= 1:
            raise ValueError("stability must be in [0, 1].")
        if not 0 <= self.state.battery_energy_wh <= self.params.battery_capacity_wh:
            raise ValueError("battery_energy_wh must be within battery capacity.")


@dataclass(slots=True)
class EnergyTurnInput:
    solar_power_w: float
    load_power_w: float
    dt_hour: float

    def validate(self) -> None:
        if self.solar_power_w < 0:
            raise ValueError("solar_power_w must be non-negative.")
        if self.load_power_w < 0:
            raise ValueError("load_power_w must be non-negative.")
        if self.dt_hour <= 0:
            raise ValueError("dt_hour must be positive.")


@dataclass(slots=True)
class EnergyTurnResult:
    colony_id: str
    served_load_wh: float
    unmet_load_wh: float
    solar_used_wh: float
    curtailed_solar_wh: float
    battery_energy_wh: float
    battery_delta_wh: float
    loss_wh: float
    service_ratio: float
    energy_score: float
    oak_accepted: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EnergyCivilizationEngine:
    """Turn-based energy civilization layer built on MicrogridStep."""

    world: WorldGraph = field(default_factory=WorldGraph)
    gm: GameMasterAgent = field(default_factory=GameMasterAgent)
    rule_kernel: RuleKernel = field(default_factory=RuleKernel)
    sandbox: ScienceSandboxEngine | None = None
    colonies: dict[str, EnergyColony] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sandbox is None:
            self.sandbox = ScienceSandboxEngine(world=self.world, gm=self.gm, rule_kernel=self.rule_kernel)
        if "energy_civilization" not in self.world.entities:
            self.world.add_entity(
                Entity(
                    entity_id="energy_civilization",
                    kind="simulation_layer",
                    name="EnergyCivilization-T",
                    attributes={"oak_mode": "educational_microgrid_strategy", "power": 0.5},
                )
            )

    def add_colony(self, colony: EnergyColony) -> None:
        if colony.colony_id in self.colonies:
            raise ValueError(f"Colony already exists: {colony.colony_id}")
        self.colonies[colony.colony_id] = colony
        self.world.add_entity(
            Entity(
                entity_id=colony.colony_id,
                kind="energy_colony",
                name=colony.name,
                attributes={
                    "battery_energy_wh": colony.state.battery_energy_wh,
                    "battery_capacity_wh": colony.params.battery_capacity_wh,
                    "population": colony.population,
                    "stability": colony.stability,
                    "power": colony.stability,
                },
            )
        )
        self.world.add_relation("energy_civilization", "contains", colony.colony_id)

    def play_turn(self, colony_id: str, turn: EnergyTurnInput) -> EnergyTurnResult:
        if colony_id not in self.colonies:
            raise KeyError(f"Unknown energy colony: {colony_id}")
        turn.validate()
        colony = self.colonies[colony_id]

        step = self.sandbox.step_microgrid(
            state=colony.state,
            params=colony.params,
            solar_power_w=turn.solar_power_w,
            load_power_w=turn.load_power_w,
            dt_hour=turn.dt_hour,
        )
        colony.state = step.state

        requested_load_wh = turn.load_power_w * turn.dt_hour
        service_ratio = 1.0 if requested_load_wh == 0 else step.served_load_wh / requested_load_wh
        energy_score = self._score_turn(
            service_ratio=service_ratio,
            loss_wh=step.loss_wh,
            unmet_load_wh=step.unmet_load_wh,
            curtailed_solar_wh=step.curtailed_solar_wh,
            requested_load_wh=max(1.0, requested_load_wh),
        )
        colony.stability = max(0.0, min(1.0, 0.8 * colony.stability + 0.2 * service_ratio))

        event = Event(
            event_id=f"energy_turn_{colony_id}_{len(self.world.memory) + 1}",
            kind="energy_turn",
            description=f"Energy turn for {colony.name}",
            actors=["energy_civilization"],
            targets=[colony_id],
            payload={
                "service_ratio": service_ratio,
                "energy_score": energy_score,
                "served_load_wh": step.served_load_wh,
                "unmet_load_wh": step.unmet_load_wh,
                "loss_wh": step.loss_wh,
                "battery_energy_wh": step.state.battery_energy_wh,
                "fair": True,
                "fun": True,
                "agency": 0.8,
                "metric": "energy_score_and_service_ratio",
                "expected_signal": "colony stability tracks served energy demand",
                "risk_flags": [],
            },
        )
        report = self.gm.oak_gate.validate(self.world, event, self.rule_kernel)

        result = EnergyTurnResult(
            colony_id=colony_id,
            served_load_wh=step.served_load_wh,
            unmet_load_wh=step.unmet_load_wh,
            solar_used_wh=step.solar_used_wh,
            curtailed_solar_wh=step.curtailed_solar_wh,
            battery_energy_wh=step.state.battery_energy_wh,
            battery_delta_wh=step.battery_delta_wh,
            loss_wh=step.loss_wh,
            service_ratio=service_ratio,
            energy_score=energy_score,
            oak_accepted=report.accepted,
            reasons=report.reasons,
        )
        payload = asdict(result)

        self.world.entities[colony_id].attributes["battery_energy_wh"] = colony.state.battery_energy_wh
        self.world.entities[colony_id].attributes["stability"] = colony.stability
        self.world.entities[colony_id].attributes["power"] = colony.stability

        if report.accepted and service_ratio >= 0.95:
            self.gm.m_plus.record("energy_turn_served", payload)
        elif report.accepted:
            self.gm.m_minus.record("energy_turn_unserved_load", payload)
        else:
            self.gm.m_minus.record("oak_rejected_energy_turn", payload)

        self.world.remember(
            {
                "type": "energy_turn",
                "colony_id": colony_id,
                "result": payload,
                "oak": report.metrics,
            }
        )
        return result

    def tick_gm(self) -> GMProposal:
        return self.gm.step(self.world, self.rule_kernel)

    @staticmethod
    def _score_turn(
        service_ratio: float,
        loss_wh: float,
        unmet_load_wh: float,
        curtailed_solar_wh: float,
        requested_load_wh: float,
    ) -> float:
        loss_penalty = 0.25 * loss_wh / requested_load_wh
        unmet_penalty = 0.75 * unmet_load_wh / requested_load_wh
        curtailment_penalty = 0.10 * curtailed_solar_wh / requested_load_wh
        return max(0.0, min(1.0, service_ratio - loss_penalty - unmet_penalty - curtailment_penalty))

    @classmethod
    def demo_civilization(cls) -> "EnergyCivilizationEngine":
        engine = cls()
        engine.add_colony(
            EnergyColony(
                colony_id="colony_solar_1",
                name="Colonie solaire 1",
                state=MicrogridState(battery_energy_wh=250.0),
                params=MicrogridParams(
                    battery_capacity_wh=1000.0,
                    roundtrip_efficiency=0.9,
                    max_charge_power_w=400.0,
                    max_discharge_power_w=400.0,
                ),
                population=120,
                stability=0.8,
            )
        )
        return engine


__all__ = ["EnergyCivilizationEngine", "EnergyColony", "EnergyTurnInput", "EnergyTurnResult"]
