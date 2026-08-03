from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Callable, Sequence

from .cosim import ClosedLoopReport, ClosedLoopSample, FaultEvent


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _trapz(samples: Sequence[ClosedLoopSample], function: Callable[[ClosedLoopSample], float]) -> float:
    total = 0.0
    for left, right in zip(samples, samples[1:]):
        dt = right.time_s - left.time_s
        if dt < 0:
            raise ValueError("sample times must be monotonic")
        total += 0.5 * dt * (function(left) + function(right))
    return total


def _active_fault_value(faults: Sequence[FaultEvent], time_s: float, field: str, default: float) -> float:
    value = default
    for fault in faults:
        if not fault.active(time_s):
            continue
        item = float(getattr(fault, field))
        if field in ("motor_force_scale", "voltage_scale", "compute_time_scale"):
            value *= item
        else:
            value += item
    return value


@dataclass(frozen=True)
class EnergyTerm:
    term_id: str
    category: str
    energy_j: float
    expected_sign: str
    interpretation: str
    intermediate_conversion: bool = False

    def validate(self) -> None:
        if not self.term_id.strip() or not self.category.strip() or not self.interpretation.strip():
            raise ValueError("energy term identifiers and interpretation are required")
        if self.expected_sign not in ("nonnegative", "signed", "zero"):
            raise ValueError("unknown energy-term sign expectation")
        if not isfinite(self.energy_j):
            raise ValueError("energy term must be finite")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class DomainBalance:
    balance_id: str
    supplied_energy_j: float
    accounted_energy_j: float
    residual_j: float
    normalized_residual: float
    tolerance_j: float
    passed: bool
    terms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["terms"] = list(self.terms)
        return payload


@dataclass(frozen=True)
class PassivityAssessment:
    classification: str
    nonnegative_dissipation_satisfied: bool
    negative_dissipation_candidate_j: float
    conversion_loss_j: float
    bidirectional_conversion_observed: bool
    energy_creation_candidate_j: float
    tolerance_j: float
    passivity_proven: bool = False
    physical_validation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EnergyGraphReport:
    scenario_id: str
    source_report_hash: str
    terms: tuple[EnergyTerm, ...]
    balances: tuple[DomainBalance, ...]
    global_supplied_energy_j: float
    global_accounted_energy_j: float
    global_residual_j: float
    global_normalized_residual: float
    absolute_source_energy_j: float
    residual_tolerance_j: float
    balance_passed: bool
    passivity: PassivityAssessment
    sample_count: int
    finite: bool
    evidence_hash: str
    energy_conservation_proven: bool = False
    physics_certified: bool = False
    hardware_validated: bool = False

    def term(self, term_id: str) -> EnergyTerm:
        for term in self.terms:
            if term.term_id == term_id:
                return term
        raise KeyError(term_id)

    def balance(self, balance_id: str) -> DomainBalance:
        for balance in self.balances:
            if balance.balance_id == balance_id:
                return balance
        raise KeyError(balance_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "source_report_hash": self.source_report_hash,
            "terms": [item.to_dict() for item in self.terms],
            "balances": [item.to_dict() for item in self.balances],
            "global_supplied_energy_j": self.global_supplied_energy_j,
            "global_accounted_energy_j": self.global_accounted_energy_j,
            "global_residual_j": self.global_residual_j,
            "global_normalized_residual": self.global_normalized_residual,
            "absolute_source_energy_j": self.absolute_source_energy_j,
            "residual_tolerance_j": self.residual_tolerance_j,
            "balance_passed": self.balance_passed,
            "passivity": self.passivity.to_dict(),
            "sample_count": self.sample_count,
            "finite": self.finite,
            "evidence_hash": self.evidence_hash,
            "energy_conservation_proven": self.energy_conservation_proven,
            "physics_certified": self.physics_certified,
            "hardware_validated": self.hardware_validated,
            "limitations": [
                "audit checks algebraic consistency of the declared lumped model only",
                "trapezoidal integration and finite sampling introduce numerical residuals",
                "conversion residual combines transmission loss, motor-constant mismatch and unmodelled fault effects",
                "negative aggregate conversion loss makes passivity inconclusive rather than proving active energy generation",
                "no calibration, measured uncertainty, hardware loss map or regulatory evidence is present",
            ],
        }


def _balance(
    balance_id: str,
    supplied: float,
    accounted: float,
    *,
    absolute_reference: float,
    tolerance_fraction: float,
    minimum_tolerance_j: float,
    terms: tuple[str, ...],
) -> DomainBalance:
    residual = supplied - accounted
    reference = max(abs(supplied), abs(accounted), absolute_reference, 1e-12)
    tolerance = max(minimum_tolerance_j, tolerance_fraction * reference)
    return DomainBalance(
        balance_id=balance_id,
        supplied_energy_j=supplied,
        accounted_energy_j=accounted,
        residual_j=residual,
        normalized_residual=abs(residual) / reference,
        tolerance_j=tolerance,
        passed=abs(residual) <= tolerance,
        terms=terms,
    )


def audit_closed_loop_energy(
    report: ClosedLoopReport,
    *,
    residual_tolerance_fraction: float = 0.02,
    minimum_tolerance_j: float = 0.02,
    untracked_output_energy_j: float = 0.0,
) -> EnergyGraphReport:
    if residual_tolerance_fraction <= 0 or minimum_tolerance_j <= 0:
        raise ValueError("energy-audit tolerances must be positive")
    if untracked_output_energy_j < 0:
        raise ValueError("untracked_output_energy_j cannot be negative")
    samples = report.samples
    if len(samples) < 2:
        raise ValueError("energy audit requires at least two samples")
    plant = report.plant
    scenario = report.scenario

    electrical_input = _trapz(samples, lambda item: item.electrical_power_w)
    absolute_source = _trapz(samples, lambda item: abs(item.electrical_power_w))
    copper_loss = _trapz(samples, lambda item: plant.resistance_ohm * item.current_a * item.current_a)
    cooling_loss = _trapz(
        samples,
        lambda item: (item.motor_temperature_k - plant.ambient_temperature_k) / plant.thermal_resistance_k_w,
    )
    damping_loss = _trapz(samples, lambda item: plant.damping_n_s_m * item.velocity_mps * item.velocity_mps)
    external_work = _trapz(
        samples,
        lambda item: (
            scenario.external_force_n
            + _active_fault_value(scenario.faults, item.time_s, "external_force_n", 0.0)
        )
        * item.velocity_mps,
    )
    electromagnetic_conversion = _trapz(
        samples,
        lambda item: (
            plant.back_emf_v_s_rad
            * plant.motor_rad_per_m
            * item.velocity_mps
            * item.current_a
        ),
    )
    mechanical_delivery = _trapz(samples, lambda item: item.mechanical_power_w)
    conversion_residual = electromagnetic_conversion - mechanical_delivery

    first = samples[0]
    last = samples[-1]
    magnetic_storage_change = 0.5 * plant.inductance_h * (
        last.current_a * last.current_a - first.current_a * first.current_a
    )
    kinetic_storage_change = 0.5 * plant.mass_kg * (
        last.velocity_mps * last.velocity_mps - first.velocity_mps * first.velocity_mps
    )
    spring_storage_change = 0.5 * plant.stiffness_n_m * (
        last.true_position_m * last.true_position_m - first.true_position_m * first.true_position_m
    )
    thermal_storage_change = plant.thermal_capacitance_j_k * (
        last.motor_temperature_k - first.motor_temperature_k
    )

    terms = (
        EnergyTerm("electrical_source", "supply", electrical_input, "signed", "integral of applied voltage times armature current"),
        EnergyTerm("magnetic_storage_change", "storage", magnetic_storage_change, "signed", "change in inductor magnetic energy"),
        EnergyTerm("copper_loss", "dissipation", copper_loss, "nonnegative", "integral of armature I^2R loss"),
        EnergyTerm("electromagnetic_conversion", "conversion", electromagnetic_conversion, "signed", "back-EMF power transferred from electrical dynamics", True),
        EnergyTerm("mechanical_delivery", "conversion", mechanical_delivery, "signed", "force-velocity power delivered by the transmission model", True),
        EnergyTerm("conversion_residual", "dissipation_or_model_residue", conversion_residual, "nonnegative", "electromagnetic conversion minus delivered mechanical work"),
        EnergyTerm("kinetic_storage_change", "storage", kinetic_storage_change, "signed", "change in translational kinetic energy"),
        EnergyTerm("spring_storage_change", "storage", spring_storage_change, "signed", "change in elastic potential energy"),
        EnergyTerm("damping_loss", "dissipation", damping_loss, "nonnegative", "integral of viscous damping power"),
        EnergyTerm("external_work", "external_work", external_work, "signed", "work performed against declared external load"),
        EnergyTerm("thermal_storage_change", "storage", thermal_storage_change, "signed", "change in lumped motor thermal energy"),
        EnergyTerm("cooling_loss", "dissipation", cooling_loss, "nonnegative", "heat transferred to the declared ambient"),
        EnergyTerm("untracked_output", "adversarial_probe", untracked_output_energy_j, "nonnegative", "explicit audit probe representing untracked output energy"),
    )

    electrical_balance = _balance(
        "electrical",
        electrical_input,
        magnetic_storage_change + copper_loss + electromagnetic_conversion,
        absolute_reference=absolute_source,
        tolerance_fraction=residual_tolerance_fraction,
        minimum_tolerance_j=minimum_tolerance_j,
        terms=("electrical_source", "magnetic_storage_change", "copper_loss", "electromagnetic_conversion"),
    )
    thermal_balance = _balance(
        "thermal",
        copper_loss,
        thermal_storage_change + cooling_loss,
        absolute_reference=max(abs(copper_loss), 1e-12),
        tolerance_fraction=residual_tolerance_fraction,
        minimum_tolerance_j=minimum_tolerance_j,
        terms=("copper_loss", "thermal_storage_change", "cooling_loss"),
    )
    mechanical_balance = _balance(
        "mechanical",
        mechanical_delivery,
        kinetic_storage_change + spring_storage_change + damping_loss + external_work,
        absolute_reference=max(abs(mechanical_delivery), 1e-12),
        tolerance_fraction=residual_tolerance_fraction,
        minimum_tolerance_j=minimum_tolerance_j,
        terms=("mechanical_delivery", "kinetic_storage_change", "spring_storage_change", "damping_loss", "external_work"),
    )

    global_accounted = (
        magnetic_storage_change
        + thermal_storage_change
        + cooling_loss
        + conversion_residual
        + kinetic_storage_change
        + spring_storage_change
        + damping_loss
        + external_work
        + untracked_output_energy_j
    )
    global_balance = _balance(
        "global",
        electrical_input,
        global_accounted,
        absolute_reference=absolute_source,
        tolerance_fraction=residual_tolerance_fraction,
        minimum_tolerance_j=minimum_tolerance_j,
        terms=(
            "electrical_source", "magnetic_storage_change", "thermal_storage_change", "cooling_loss",
            "conversion_residual", "kinetic_storage_change", "spring_storage_change", "damping_loss",
            "external_work", "untracked_output",
        ),
    )
    balances = (electrical_balance, thermal_balance, mechanical_balance, global_balance)

    dissipations = (copper_loss, cooling_loss, damping_loss)
    negative_dissipation = sum(max(0.0, -item) for item in dissipations)
    tolerance = global_balance.tolerance_j
    bidirectional = conversion_residual < -tolerance
    energy_creation_candidate = max(0.0, -conversion_residual) + negative_dissipation
    if not global_balance.passed:
        classification = "RESIDUAL_EXCEEDS_TOLERANCE"
    elif bidirectional:
        classification = "INCONCLUSIVE_BIDIRECTIONAL_CONVERSION"
    elif negative_dissipation > tolerance:
        classification = "NEGATIVE_DISSIPATION_CANDIDATE"
    else:
        classification = "PASSIVE_WITHIN_DECLARED_LUMPED_MODEL"
    passivity = PassivityAssessment(
        classification=classification,
        nonnegative_dissipation_satisfied=negative_dissipation <= tolerance,
        negative_dissipation_candidate_j=negative_dissipation,
        conversion_loss_j=conversion_residual,
        bidirectional_conversion_observed=bidirectional,
        energy_creation_candidate_j=energy_creation_candidate,
        tolerance_j=tolerance,
    )
    finite = all(isfinite(item.energy_j) for item in terms) and all(
        isfinite(value)
        for balance in balances
        for value in (
            balance.supplied_energy_j,
            balance.accounted_energy_j,
            balance.residual_j,
            balance.normalized_residual,
        )
    )
    stable = {
        "scenario_id": scenario.scenario_id,
        "source_report_hash": report.evidence_hash,
        "terms": [item.to_dict() for item in terms],
        "balances": [item.to_dict() for item in balances],
        "passivity": passivity.to_dict(),
        "sample_count": len(samples),
    }
    return EnergyGraphReport(
        scenario_id=scenario.scenario_id,
        source_report_hash=report.evidence_hash,
        terms=terms,
        balances=balances,
        global_supplied_energy_j=electrical_input,
        global_accounted_energy_j=global_accounted,
        global_residual_j=global_balance.residual_j,
        global_normalized_residual=global_balance.normalized_residual,
        absolute_source_energy_j=absolute_source,
        residual_tolerance_j=global_balance.tolerance_j,
        balance_passed=all(item.passed for item in balances),
        passivity=passivity,
        sample_count=len(samples),
        finite=finite,
        evidence_hash=_stable_hash(stable),
    )
