"""ScienceSandbox-T: OAK-safe scientific play/simulation engine.

The models here are intentionally minimal and dependency-free. They are not
validated engineering solvers. They are playable, inspectable teaching and
prototype models that keep units, residues and OAK safety visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from ..core import Entity, Event, RuleKernel, WorldGraph
from ..gm import GameMasterAgent, GMProposal


@dataclass(slots=True)
class RLCState:
    """State for a simple series RLC circuit.

    q_coulomb: capacitor charge Q.
    i_ampere: circuit current I.
    t_second: simulated time.
    """

    q_coulomb: float = 0.0
    i_ampere: float = 0.0
    t_second: float = 0.0


@dataclass(slots=True)
class RLCParams:
    resistance_ohm: float
    inductance_henry: float
    capacitance_farad: float
    source_voltage_volt: float = 0.0

    def validate(self) -> None:
        if self.resistance_ohm < 0:
            raise ValueError("Resistance must be non-negative.")
        if self.inductance_henry <= 0:
            raise ValueError("Inductance must be positive.")
        if self.capacitance_farad <= 0:
            raise ValueError("Capacitance must be positive.")


@dataclass(slots=True)
class RLCStepResult:
    state: RLCState
    capacitor_energy_joule: float
    inductor_energy_joule: float
    joule_loss_joule: float
    source_work_joule: float
    energy_residue_joule: float


@dataclass(slots=True)
class MicrogridState:
    battery_energy_wh: float
    t_hour: float = 0.0


@dataclass(slots=True)
class MicrogridParams:
    battery_capacity_wh: float
    roundtrip_efficiency: float = 0.9
    max_charge_power_w: float = 500.0
    max_discharge_power_w: float = 500.0

    def validate(self) -> None:
        if self.battery_capacity_wh <= 0:
            raise ValueError("Battery capacity must be positive.")
        if not 0 < self.roundtrip_efficiency <= 1:
            raise ValueError("Roundtrip efficiency must be in (0, 1].")
        if self.max_charge_power_w < 0 or self.max_discharge_power_w < 0:
            raise ValueError("Charge/discharge power limits must be non-negative.")


@dataclass(slots=True)
class MicrogridStepResult:
    state: MicrogridState
    served_load_wh: float
    unmet_load_wh: float
    solar_used_wh: float
    curtailed_solar_wh: float
    battery_delta_wh: float
    loss_wh: float


@dataclass(slots=True)
class ScienceSandboxEngine:
    """Minimal ScienceSandbox-T world layer.

    It exposes deterministic step functions and also records accepted simulation
    events into the Ω-GAME-T world memory.
    """

    world: WorldGraph = field(default_factory=WorldGraph)
    gm: GameMasterAgent = field(default_factory=GameMasterAgent)
    rule_kernel: RuleKernel = field(default_factory=RuleKernel)

    def __post_init__(self) -> None:
        if "science_sandbox" not in self.world.entities:
            self.world.add_entity(
                Entity(
                    entity_id="science_sandbox",
                    kind="lab",
                    name="ScienceSandbox-T",
                    attributes={"oak_mode": "educational_simulation", "power": 0.5},
                )
            )

    def step_rlc(self, state: RLCState, params: RLCParams, dt_second: float) -> RLCStepResult:
        params.validate()
        self._require_positive_step(dt_second, "dt_second")

        old_cap_energy = self._capacitor_energy(state.q_coulomb, params.capacitance_farad)
        old_ind_energy = self._inductor_energy(state.i_ampere, params.inductance_henry)

        # Series RLC equation: L dI/dt + R I + Q/C = V_source.
        di_dt = (
            params.source_voltage_volt
            - params.resistance_ohm * state.i_ampere
            - state.q_coulomb / params.capacitance_farad
        ) / params.inductance_henry

        new_i = state.i_ampere + di_dt * dt_second
        new_q = state.q_coulomb + new_i * dt_second
        new_state = RLCState(q_coulomb=new_q, i_ampere=new_i, t_second=state.t_second + dt_second)

        new_cap_energy = self._capacitor_energy(new_q, params.capacitance_farad)
        new_ind_energy = self._inductor_energy(new_i, params.inductance_henry)
        joule_loss = params.resistance_ohm * (state.i_ampere**2) * dt_second
        source_work = params.source_voltage_volt * state.i_ampere * dt_second
        energy_delta = (new_cap_energy + new_ind_energy) - (old_cap_energy + old_ind_energy)
        residue = source_work - joule_loss - energy_delta

        result = RLCStepResult(
            state=new_state,
            capacitor_energy_joule=new_cap_energy,
            inductor_energy_joule=new_ind_energy,
            joule_loss_joule=joule_loss,
            source_work_joule=source_work,
            energy_residue_joule=residue,
        )
        self._record_science_event(
            kind="rlc_step",
            description="ScienceSandbox-T RLC step",
            payload={
                "metric": "rlc_energy_residue_joule",
                "expected_signal": "bounded energy residue for small dt",
                "energy_residue_joule": residue,
                "risk_flags": [],
                "fair": True,
                "fun": True,
                "agency": 0.7,
            },
        )
        return result

    def step_microgrid(
        self,
        state: MicrogridState,
        params: MicrogridParams,
        solar_power_w: float,
        load_power_w: float,
        dt_hour: float,
    ) -> MicrogridStepResult:
        params.validate()
        self._require_positive_step(dt_hour, "dt_hour")
        if solar_power_w < 0 or load_power_w < 0:
            raise ValueError("Solar and load power must be non-negative.")

        solar_wh = solar_power_w * dt_hour
        load_wh = load_power_w * dt_hour
        direct_solar_to_load = min(solar_wh, load_wh)
        remaining_load = load_wh - direct_solar_to_load
        surplus_solar = solar_wh - direct_solar_to_load

        # Split round-trip efficiency symmetrically for a simple educational model.
        charge_efficiency = params.roundtrip_efficiency**0.5
        discharge_efficiency = params.roundtrip_efficiency**0.5

        max_charge_wh = params.max_charge_power_w * dt_hour
        available_capacity_wh = max(0.0, params.battery_capacity_wh - state.battery_energy_wh)
        charge_input_wh = min(surplus_solar, max_charge_wh, available_capacity_wh / charge_efficiency)
        stored_wh = charge_input_wh * charge_efficiency

        max_discharge_wh = params.max_discharge_power_w * dt_hour
        battery_output_needed_wh = remaining_load / discharge_efficiency if discharge_efficiency > 0 else 0.0
        battery_discharge_wh = min(state.battery_energy_wh, max_discharge_wh, battery_output_needed_wh)
        served_from_battery_wh = battery_discharge_wh * discharge_efficiency

        new_battery_energy = state.battery_energy_wh + stored_wh - battery_discharge_wh
        new_battery_energy = min(params.battery_capacity_wh, max(0.0, new_battery_energy))

        served_load = direct_solar_to_load + served_from_battery_wh
        unmet_load = max(0.0, load_wh - served_load)
        curtailed_solar = max(0.0, surplus_solar - charge_input_wh)
        loss_wh = max(0.0, charge_input_wh - stored_wh) + max(
            0.0, battery_discharge_wh - served_from_battery_wh
        )

        result = MicrogridStepResult(
            state=MicrogridState(battery_energy_wh=new_battery_energy, t_hour=state.t_hour + dt_hour),
            served_load_wh=served_load,
            unmet_load_wh=unmet_load,
            solar_used_wh=direct_solar_to_load + charge_input_wh,
            curtailed_solar_wh=curtailed_solar,
            battery_delta_wh=new_battery_energy - state.battery_energy_wh,
            loss_wh=loss_wh,
        )
        self._record_science_event(
            kind="microgrid_step",
            description="ScienceSandbox-T microgrid step",
            payload={
                "metric": "microgrid_unmet_load_and_losses",
                "expected_signal": "served load, losses and battery state remain bounded",
                "unmet_load_wh": unmet_load,
                "loss_wh": loss_wh,
                "risk_flags": [],
                "fair": True,
                "fun": True,
                "agency": 0.7,
            },
        )
        return result

    def tick_gm(self) -> GMProposal:
        return self.gm.step(self.world, self.rule_kernel)

    def _record_science_event(self, kind: str, description: str, payload: dict[str, object]) -> None:
        event = Event(
            event_id=f"science_{kind}_{len(self.world.memory) + 1}",
            kind=kind,
            description=description,
            actors=["science_sandbox"],
            targets=[],
            payload=payload,
        )
        report = self.gm.oak_gate.validate(self.world, event, self.rule_kernel)
        if report.accepted:
            self.world.remember(
                {
                    "type": kind,
                    "description": description,
                    "payload": payload,
                    "oak": report.metrics,
                }
            )
            self.gm.m_plus.record(f"accepted_{kind}", dict(payload))
        else:
            self.gm.m_minus.record(f"rejected_{kind}", {"reasons": report.reasons, "payload": payload})

    @staticmethod
    def _capacitor_energy(q_coulomb: float, capacitance_farad: float) -> float:
        return 0.5 * (q_coulomb**2) / capacitance_farad

    @staticmethod
    def _inductor_energy(i_ampere: float, inductance_henry: float) -> float:
        return 0.5 * inductance_henry * (i_ampere**2)

    @staticmethod
    def _require_positive_step(value: float, name: str) -> None:
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive.")


__all__ = [
    "MicrogridParams",
    "MicrogridState",
    "MicrogridStepResult",
    "RLCParams",
    "RLCState",
    "RLCStepResult",
    "ScienceSandboxEngine",
]
