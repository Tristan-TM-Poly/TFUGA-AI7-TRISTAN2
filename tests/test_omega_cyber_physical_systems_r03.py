from __future__ import annotations

import json

import pytest

from omega_cyber_physical_systems_t.hybrid import (
    AffineFlow,
    HybridAutomaton,
    HybridMode,
    HybridTransition,
    Predicate,
    ResetRule,
    demo_zeno_automaton,
    simulate_hybrid_automaton,
)
from omega_cyber_physical_systems_t.r03_cli import main as r03_main
from omega_cyber_physical_systems_t.r03_fixtures import (
    r03_adversarial_initial_box,
    r03_axis_automaton,
    r03_initial_box,
    r03_temporal_properties,
    r03_unsafe_condition,
)
from omega_cyber_physical_systems_t.r03_oak import run_cps_r03_benchmarks
from omega_cyber_physical_systems_t.reachability import (
    Interval,
    ReachBox,
    bounded_reachability,
)
from omega_cyber_physical_systems_t.temporal import (
    TemporalProperty,
    evaluate_temporal_property,
    verify_temporal_properties,
)


def test_predicate_comparators_and_margin() -> None:
    state = {"x": 2.0}
    assert Predicate("x", ">=", 2.0).evaluate(state)
    assert Predicate("x", "<=", 2.0).evaluate(state)
    assert Predicate("x", "==", 2.0).evaluate(state)
    assert Predicate("x", "!=", 3.0).evaluate(state)
    assert Predicate("x", ">=", 1.5).signed_margin(state) == pytest.approx(0.5)


def test_predicate_rejects_unknown_comparator() -> None:
    with pytest.raises(ValueError):
        Predicate("x", "approximately", 1.0).validate()


def test_affine_flow_evaluates_declared_state() -> None:
    flow = AffineFlow(1.0, {"x": 2.0, "y": -1.0})
    flow.validate(("x", "y"))
    assert flow.evaluate({"x": 3.0, "y": 4.0}) == pytest.approx(3.0)


def test_reset_rule_uses_pre_transition_state() -> None:
    reset = ResetRule("x", "y", scale=2.0, offset=1.0)
    reset.validate(("x", "y"))
    assert reset.apply({"x": 9.0, "y": 3.0}) == pytest.approx(7.0)


def test_axis_automaton_validates_and_hashes_deterministically() -> None:
    first = r03_axis_automaton()
    second = r03_axis_automaton()
    first.validate()
    assert first.evidence_hash == second.evidence_hash
    assert len(first.evidence_hash) == 64
    assert first.permanent_total_cap is None
    assert first.physics_certified is False
    assert first.safety_certified is False


def test_automaton_rejects_incomplete_flows() -> None:
    mode = HybridMode("m", {"x": AffineFlow()})
    automaton = HybridAutomaton(
        automaton_id="bad",
        variables=("x", "y"),
        modes=(mode,),
        transitions=(),
        initial_mode="m",
        initial_state={"x": 0.0, "y": 0.0},
        safe_modes=("m",),
    )
    with pytest.raises(ValueError):
        automaton.validate()


def test_nominal_hybrid_trace_is_finite_and_invariant_clean() -> None:
    report = simulate_hybrid_automaton(
        r03_axis_automaton(),
        horizon_s=1.30,
        integration_step_s=0.001,
    )
    assert report.finite
    assert report.invariant_violation_count == 0
    assert report.unsafe_sample_count == 0
    assert report.final_mode == "safe_shutdown"
    assert len(report.samples) == 1301


def test_nominal_transition_sequence_is_exact() -> None:
    report = simulate_hybrid_automaton(
        r03_axis_automaton(),
        horizon_s=1.30,
        integration_step_s=0.001,
    )
    assert tuple(item.transition_id for item in report.events) == (
        "startup-complete",
        "thermal-derate",
        "timed-safe-shutdown",
    )


def test_hybrid_trace_is_deterministic() -> None:
    automaton = r03_axis_automaton()
    first = simulate_hybrid_automaton(automaton, horizon_s=1.30, integration_step_s=0.001)
    second = simulate_hybrid_automaton(automaton, horizon_s=1.30, integration_step_s=0.001)
    assert first.evidence_hash == second.evidence_hash
    assert first.final_state == second.final_state


def test_zeno_cycle_is_stopped_by_transition_guard() -> None:
    report = simulate_hybrid_automaton(
        demo_zeno_automaton(),
        horizon_s=0.1,
        integration_step_s=0.01,
        max_transitions_per_step=8,
        zeno_window_s=0.02,
        zeno_transition_threshold=6,
    )
    assert report.transition_limit_hit or report.zeno_suspected
    assert len(report.events) == 8


def test_temporal_fixture_properties_pass() -> None:
    trace = simulate_hybrid_automaton(r03_axis_automaton(), horizon_s=1.30, integration_step_s=0.001)
    report = verify_temporal_properties(trace, r03_temporal_properties())
    assert report.passed
    assert report.property_count == 4
    assert report.passed_count == 4
    assert report.violation_count == 0
    assert report.formal_proof is False
    assert report.safety_certified is False


def test_temporal_eventually_negative_control_fails_with_witness() -> None:
    trace = simulate_hybrid_automaton(r03_axis_automaton(), horizon_s=0.3, integration_step_s=0.001)
    property = TemporalProperty(
        "impossible",
        "EVENTUALLY",
        "unreachable cryogenic target",
        predicate=Predicate("temperature_k", "<=", 100.0),
        within_s=0.2,
    )
    result = evaluate_temporal_property(trace, property)
    assert not result.passed
    assert result.violation_count == 1
    assert result.first_violation is not None


def test_temporal_response_requires_a_trigger() -> None:
    trace = simulate_hybrid_automaton(r03_axis_automaton(), horizon_s=0.1, integration_step_s=0.001)
    property = TemporalProperty(
        "no-trigger",
        "RESPONSE",
        "requires thermal trigger",
        trigger=Predicate("temperature_k", ">=", 500.0),
        response_mode="derated",
        within_s=0.1,
    )
    result = evaluate_temporal_property(trace, property)
    assert not result.passed
    assert result.trigger_count == 0


def test_temporal_property_validation_rejects_incomplete_response() -> None:
    with pytest.raises(ValueError):
        TemporalProperty("bad", "RESPONSE", "missing response", trigger_mode="tracking").validate()


def test_interval_arithmetic_is_order_safe() -> None:
    interval = Interval(-2.0, 3.0)
    assert interval.scale(-2.0) == Interval(-6.0, 4.0)
    assert interval.add(Interval(1.0, 2.0)) == Interval(-1.0, 5.0)
    assert interval.widen(0.5) == Interval(-2.5, 3.5)


def test_reach_box_requires_exact_variable_cover() -> None:
    with pytest.raises(ValueError):
        ReachBox({"x": Interval(0.0, 1.0)}).validate(("x", "y"))


def test_nominal_reachability_completes_without_unsafe_box() -> None:
    report = bounded_reachability(
        r03_axis_automaton(),
        initial_box=r03_initial_box(),
        integration_step_s=0.05,
        steps=24,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=4096,
        numerical_widening_per_step=1e-8,
    )
    assert report.steps_completed == 24
    assert report.node_count > 24
    assert report.transition_branch_count >= 3
    assert report.unsafe_possible_count == 0
    assert report.unsafe_definite_count == 0
    assert not report.truncated
    assert report.permanent_total_cap is None
    assert report.formal_reachability_proven is False


def test_reachability_is_deterministic() -> None:
    kwargs = dict(
        initial_box=r03_initial_box(),
        integration_step_s=0.05,
        steps=24,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=4096,
        numerical_widening_per_step=1e-8,
    )
    first = bounded_reachability(r03_axis_automaton(), **kwargs)
    second = bounded_reachability(r03_axis_automaton(), **kwargs)
    assert first.evidence_hash == second.evidence_hash


def test_adversarial_reachability_detects_unsafe_intersection() -> None:
    report = bounded_reachability(
        r03_axis_automaton(),
        initial_box=r03_adversarial_initial_box(),
        integration_step_s=0.01,
        steps=2,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=64,
    )
    assert report.unsafe_possible_count > 0


def test_execution_budget_can_truncate_without_becoming_permanent_cap() -> None:
    report = bounded_reachability(
        r03_axis_automaton(),
        initial_box=r03_initial_box(),
        integration_step_s=0.05,
        steps=12,
        unsafe_conditions=r03_unsafe_condition(),
        max_nodes_per_step=1,
    )
    assert report.execution_node_budget == 1
    assert report.permanent_total_cap is None


def test_r03_oakbench_passes_all_gates() -> None:
    report = run_cps_r03_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_HYBRID_TEMPORAL_REACHABILITY_R0_3"
    assert len(report.gates) == 12
    assert all(item.passed for item in report.gates)
    assert report.event_sequence == (
        "startup-complete",
        "thermal-derate",
        "timed-safe-shutdown",
    )


def test_r03_oakbench_keeps_epistemic_boundaries() -> None:
    report = run_cps_r03_benchmarks()
    assert report.physics_certified is False
    assert report.safety_certified is False
    assert report.formal_verification_proven is False
    assert report.formal_reachability_proven is False
    assert report.standards_compliance_claim is False
    assert report.hardware_validated is False
    assert report.permanent_total_cap is None


def test_r03_cli_benchmark_outputs_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert r03_main(["benchmark"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["status"].endswith("R0_3")


def test_r03_cli_hybrid_summary(capsys: pytest.CaptureFixture[str]) -> None:
    assert r03_main(["hybrid-demo", "--summary-only"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["final_mode"] == "safe_shutdown"
    assert payload["invariant_violation_count"] == 0
    assert payload["event_sequence"][-1] == "timed-safe-shutdown"


def test_r03_cli_temporal_summary(capsys: pytest.CaptureFixture[str]) -> None:
    assert r03_main(["temporal-demo", "--summary-only"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["property_count"] == 4


def test_r03_cli_adversarial_reachability_returns_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert r03_main([
        "reachability-demo",
        "--adversarial",
        "--summary-only",
        "--steps",
        "2",
        "--dt-s",
        "0.01",
    ]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["unsafe_possible_count"] > 0


def test_r03_cli_zeno_demo_reports_detection(capsys: pytest.CaptureFixture[str]) -> None:
    assert r03_main(["zeno-demo", "--summary-only"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["transition_limit_hit"] or payload["zeno_suspected"]
