from __future__ import annotations

import json

from omega_cyber_physical_systems_t.hybrid import demo_zeno_automaton, simulate_hybrid_automaton
from omega_cyber_physical_systems_t.r03_fixtures import (
    r03_adversarial_initial_box,
    r03_axis_automaton,
    r03_initial_box,
    r03_temporal_properties,
    r03_unsafe_condition,
)
from omega_cyber_physical_systems_t.r03_oak import run_cps_r03_benchmarks
from omega_cyber_physical_systems_t.reachability import bounded_reachability
from omega_cyber_physical_systems_t.temporal import verify_temporal_properties


def main() -> int:
    automaton = r03_axis_automaton()
    trace = simulate_hybrid_automaton(
        automaton,
        horizon_s=1.30,
        integration_step_s=0.001,
    )
    temporal = verify_temporal_properties(trace, r03_temporal_properties())
    reachability = bounded_reachability(
        automaton,
        initial_box=r03_initial_box(),
        integration_step_s=0.05,
        steps=24,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=4096,
        numerical_widening_per_step=1e-8,
    )
    adversarial = bounded_reachability(
        automaton,
        initial_box=r03_adversarial_initial_box(),
        integration_step_s=0.01,
        steps=2,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=64,
    )
    zeno = simulate_hybrid_automaton(
        demo_zeno_automaton(),
        horizon_s=0.1,
        integration_step_s=0.01,
        max_transitions_per_step=8,
        zeno_window_s=0.02,
        zeno_transition_threshold=6,
    )
    oak = run_cps_r03_benchmarks()
    payload = {
        "automaton": {
            "mode_count": len(automaton.modes),
            "transition_count": len(automaton.transitions),
            "evidence_hash": automaton.evidence_hash,
            "physics_certified": automaton.physics_certified,
            "safety_certified": automaton.safety_certified,
        },
        "trace": {
            "sample_count": len(trace.samples),
            "event_sequence": [item.transition_id for item in trace.events],
            "final_mode": trace.final_mode,
            "invariant_violation_count": trace.invariant_violation_count,
            "evidence_hash": trace.evidence_hash,
        },
        "temporal": {
            "property_count": temporal.property_count,
            "passed_count": temporal.passed_count,
            "violation_count": temporal.violation_count,
            "evidence_hash": temporal.evidence_hash,
            "formal_proof": temporal.formal_proof,
        },
        "reachability": {
            "node_count": reachability.node_count,
            "transition_branch_count": reachability.transition_branch_count,
            "unsafe_possible_count": reachability.unsafe_possible_count,
            "truncated": reachability.truncated,
            "evidence_hash": reachability.evidence_hash,
            "formal_reachability_proven": reachability.formal_reachability_proven,
        },
        "negative_controls": {
            "adversarial_unsafe_possible_count": adversarial.unsafe_possible_count,
            "zeno_detected": zeno.zeno_suspected or zeno.transition_limit_hit,
        },
        "oak": {
            "status": oak.status,
            "passed": oak.passed,
            "gate_count": len(oak.gates),
            "physics_certified": oak.physics_certified,
            "safety_certified": oak.safety_certified,
            "formal_verification_proven": oak.formal_verification_proven,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if oak.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
