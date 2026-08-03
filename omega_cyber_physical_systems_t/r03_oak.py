from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from .hybrid import demo_zeno_automaton, simulate_hybrid_automaton
from .r03_fixtures import (
    r03_adversarial_initial_box,
    r03_axis_automaton,
    r03_initial_box,
    r03_temporal_properties,
    r03_unsafe_condition,
)
from .reachability import bounded_reachability
from .temporal import TemporalProperty, verify_temporal_properties
from .hybrid import Predicate


@dataclass(frozen=True)
class CPSR03OAKGate:
    gate_id: str
    passed: bool
    detail: str
    measured: float | int | str | bool | None = None
    threshold: float | int | str | bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CPSR03OAKReport:
    status: str
    passed: bool
    gates: tuple[CPSR03OAKGate, ...]
    automaton_hash: str
    trace_hash: str
    temporal_hash: str
    reachability_hash: str
    zeno_trace_hash: str
    event_sequence: tuple[str, ...]
    trace_sample_count: int
    reachability_node_count: int
    physics_certified: bool = False
    safety_certified: bool = False
    formal_verification_proven: bool = False
    formal_reachability_proven: bool = False
    standards_compliance_claim: bool = False
    hardware_validated: bool = False
    permanent_total_cap: None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "gates": [item.to_dict() for item in self.gates],
            "automaton_hash": self.automaton_hash,
            "trace_hash": self.trace_hash,
            "temporal_hash": self.temporal_hash,
            "reachability_hash": self.reachability_hash,
            "zeno_trace_hash": self.zeno_trace_hash,
            "event_sequence": list(self.event_sequence),
            "trace_sample_count": self.trace_sample_count,
            "reachability_node_count": self.reachability_node_count,
            "physics_certified": self.physics_certified,
            "safety_certified": self.safety_certified,
            "formal_verification_proven": self.formal_verification_proven,
            "formal_reachability_proven": self.formal_reachability_proven,
            "standards_compliance_claim": self.standards_compliance_claim,
            "hardware_validated": self.hardware_validated,
            "permanent_total_cap": self.permanent_total_cap,
            "limitations": [
                "finite sampled traces and bounded interval exploration only",
                "explicit Euler integration without validated numerics",
                "finite-window Zeno warning rather than mathematical proof",
                "no HIL, bench, field, safety-integrity or regulatory evidence",
            ],
        }


def _hash_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_cps_r03_benchmarks() -> CPSR03OAKReport:
    automaton = r03_axis_automaton()
    automaton.validate()
    trace = simulate_hybrid_automaton(
        automaton,
        horizon_s=1.30,
        integration_step_s=0.001,
        max_transitions_per_step=8,
    )
    trace_repeat = simulate_hybrid_automaton(
        automaton,
        horizon_s=1.30,
        integration_step_s=0.001,
        max_transitions_per_step=8,
    )
    temporal = verify_temporal_properties(trace, r03_temporal_properties())
    adversarial_temporal = verify_temporal_properties(
        trace,
        (
            TemporalProperty(
                "R03-ADVERSARIAL-CRYOGENIC",
                "EVENTUALLY",
                "deliberately unreachable temperature target",
                predicate=Predicate("temperature_k", "<=", 100.0),
                within_s=0.2,
            ),
        ),
    )
    reachability = bounded_reachability(
        automaton,
        initial_box=r03_initial_box(),
        integration_step_s=0.05,
        steps=24,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=4096,
        numerical_widening_per_step=1e-8,
    )
    reachability_repeat = bounded_reachability(
        automaton,
        initial_box=r03_initial_box(),
        integration_step_s=0.05,
        steps=24,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=4096,
        numerical_widening_per_step=1e-8,
    )
    adversarial_reachability = bounded_reachability(
        automaton,
        initial_box=r03_adversarial_initial_box(),
        integration_step_s=0.01,
        steps=2,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=64,
    )
    zeno_trace = simulate_hybrid_automaton(
        demo_zeno_automaton(),
        horizon_s=0.1,
        integration_step_s=0.01,
        max_transitions_per_step=8,
        zeno_window_s=0.02,
        zeno_transition_threshold=6,
    )

    sequence = tuple(item.transition_id for item in trace.events)
    expected_sequence = (
        "startup-complete",
        "thermal-derate",
        "timed-safe-shutdown",
    )
    no_claims = not any(
        (
            trace.physics_certified,
            trace.safety_certified,
            trace.formal_reachability_proven,
            temporal.formal_proof,
            temporal.safety_certified,
            reachability.formal_reachability_proven,
            reachability.safety_certified,
        )
    )
    gates = (
        CPSR03OAKGate(
            "R03-MODEL-VALID",
            len(automaton.modes) == 4 and len(automaton.transitions) == 3,
            "hybrid fixture declares four modes and three guarded transitions",
            len(automaton.modes),
            4,
        ),
        CPSR03OAKGate(
            "R03-TRACE-FINITE",
            trace.finite and trace.invariant_violation_count == 0,
            "sampled hybrid trace remains finite and respects sampled invariants",
            trace.invariant_violation_count,
            0,
        ),
        CPSR03OAKGate(
            "R03-EVENT-SEQUENCE",
            sequence == expected_sequence,
            "transition sequence is deterministic and follows the declared fallback chain",
            ",".join(sequence),
            ",".join(expected_sequence),
        ),
        CPSR03OAKGate(
            "R03-TRACE-DETERMINISTIC",
            trace.evidence_hash == trace_repeat.evidence_hash,
            "repeated simulation produces the same SHA-256 evidence hash",
            trace.evidence_hash,
            trace_repeat.evidence_hash,
        ),
        CPSR03OAKGate(
            "R03-TEMPORAL-PROPERTIES",
            temporal.passed and temporal.passed_count == temporal.property_count,
            "all declared sampled temporal contracts pass",
            temporal.passed_count,
            temporal.property_count,
        ),
        CPSR03OAKGate(
            "R03-TEMPORAL-NEGATIVE-CONTROL",
            not adversarial_temporal.passed and adversarial_temporal.violation_count > 0,
            "unreachable adversarial property is rejected with a witness",
            adversarial_temporal.violation_count,
            1,
        ),
        CPSR03OAKGate(
            "R03-REACHABILITY-BOUNDED",
            (
                reachability.steps_completed == 24
                and not reachability.truncated
                and reachability.unsafe_possible_count == 0
                and reachability.unsafe_definite_count == 0
            ),
            "finite-horizon interval exploration completes without an unsafe box",
            reachability.unsafe_possible_count,
            0,
        ),
        CPSR03OAKGate(
            "R03-REACHABILITY-DETERMINISTIC",
            reachability.evidence_hash == reachability_repeat.evidence_hash,
            "repeated interval exploration produces the same evidence hash",
            reachability.evidence_hash,
            reachability_repeat.evidence_hash,
        ),
        CPSR03OAKGate(
            "R03-REACHABILITY-NEGATIVE-CONTROL",
            adversarial_reachability.unsafe_possible_count > 0,
            "adversarial initial box intersects the declared unsafe envelope",
            adversarial_reachability.unsafe_possible_count,
            1,
        ),
        CPSR03OAKGate(
            "R03-ZENO-GUARD",
            zeno_trace.zeno_suspected or zeno_trace.transition_limit_hit,
            "instantaneous transition cycle is stopped and reported",
            zeno_trace.transition_limit_hit,
            True,
        ),
        CPSR03OAKGate(
            "R03-NO-FALSE-CERTIFICATION",
            no_claims,
            "computational checks do not promote themselves to formal, physical or safety proof",
            no_claims,
            True,
        ),
        CPSR03OAKGate(
            "R03-NO-PERMANENT-CAP",
            reachability.permanent_total_cap is None and automaton.permanent_total_cap is None,
            "execution budgets bound a run but do not impose a permanent architecture cap",
            str(reachability.permanent_total_cap),
            "None",
        ),
    )
    passed = all(item.passed for item in gates)
    return CPSR03OAKReport(
        status=(
            "CERTIFIED_COMPUTATIONAL_HYBRID_TEMPORAL_REACHABILITY_R0_3"
            if passed
            else "FAILED_COMPUTATIONAL_HYBRID_TEMPORAL_REACHABILITY_R0_3"
        ),
        passed=passed,
        gates=gates,
        automaton_hash=automaton.evidence_hash,
        trace_hash=trace.evidence_hash,
        temporal_hash=temporal.evidence_hash,
        reachability_hash=reachability.evidence_hash,
        zeno_trace_hash=zeno_trace.evidence_hash,
        event_sequence=sequence,
        trace_sample_count=len(trace.samples),
        reachability_node_count=reachability.node_count,
    )
