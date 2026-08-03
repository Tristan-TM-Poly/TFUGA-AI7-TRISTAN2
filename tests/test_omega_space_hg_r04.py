from __future__ import annotations

import pytest

from omega_space_hg_t.reliability import (
    ComponentReliability,
    FDIRPolicy,
    FDIRState,
    FaultTreeNode,
    RadiationEnvironment,
    deterministic_uniform,
    exponential_failure_probability,
    fdir_transition,
    poisson_sample,
    run_reliability_campaign,
    simulate_reliability_trial,
    wilson_interval,
)
from omega_space_hg_t.r04 import (
    canonical_components,
    canonical_fault_tree,
    run_r04_oak_benchmarks,
    simulate_fdir_scenario,
    simulate_r04_campaign,
)


def test_deterministic_uniform_and_poisson_replay() -> None:
    assert deterministic_uniform(7, "x", 1) == deterministic_uniform(7, "x", 1)
    assert deterministic_uniform(7, "x", 1) != deterministic_uniform(7, "x", 2)
    assert poisson_sample(3.5, 42, "events") == poisson_sample(3.5, 42, "events")


def test_exponential_probability_composition() -> None:
    p1 = exponential_failure_probability(1e-4, 1000.0)
    p2 = exponential_failure_probability(1e-4, 2000.0)
    assert p2 == pytest.approx(1.0 - (1.0 - p1) ** 2, abs=1e-15)
    assert p2 > p1


def test_fault_tree_and_or_and_k_of_n() -> None:
    a = FaultTreeNode("a", "leaf", leaf_probability=0.1)
    b = FaultTreeNode("b", "leaf", leaf_probability=0.2)
    c = FaultTreeNode("c", "leaf", leaf_probability=0.3)
    assert FaultTreeNode("and", "and", (a, b)).probability() == pytest.approx(0.02)
    assert FaultTreeNode("or", "or", (a, b)).probability() == pytest.approx(0.28)
    two_of_three = FaultTreeNode("2of3", "k_of_n", (a, b, c), threshold=2)
    expected = 0.1 * 0.2 * 0.7 + 0.1 * 0.8 * 0.3 + 0.9 * 0.2 * 0.3 + 0.1 * 0.2 * 0.3
    assert two_of_three.probability() == pytest.approx(expected)


def test_radiation_expectation_is_linear() -> None:
    environment = RadiationEnvironment(0.5, 1e-8, 100, 0.25, 0.9)
    assert environment.expected_events(2000.0) == pytest.approx(
        2.0 * environment.expected_events(1000.0)
    )


def test_redundant_function_survives_one_unrecovered_component_failure() -> None:
    components = (
        ComponentReliability("a", "compute", 1e6, True, "pair", None, 1.0, 0.0),
        ComponentReliability("b", "compute", 0.0, True, "pair", None, 1.0, 0.0),
    )
    trial = simulate_reliability_trial(components, 1.0, 5)
    assert any(event.affected_components == ("a",) for event in trial.events)
    assert trial.mission_success is True
    assert trial.failed_functions == ()


def test_campaign_offsets_and_wilson_interval() -> None:
    report = run_reliability_campaign(
        canonical_components(),
        24.0,
        start_offset=10_000,
        count=128,
    )
    assert report["next_offset"] == 10_128
    assert report["permanent_total_cap"] is None
    assert 0.0 <= report["estimated_success_probability"] <= 1.0
    lower, upper = report["wilson_95_interval"]
    assert 0.0 <= lower <= upper <= 1.0
    assert wilson_interval(128, 128)[1] == pytest.approx(1.0)


def test_common_causes_reduce_canonical_success_probability() -> None:
    independent = simulate_r04_campaign(
        duration_days=365.25,
        count=2048,
        include_common_causes=False,
        include_radiation=False,
    )
    coupled = simulate_r04_campaign(
        duration_days=365.25,
        count=2048,
        include_common_causes=True,
        include_radiation=False,
    )
    assert coupled["estimated_success_probability"] < independent["estimated_success_probability"]


def test_fdir_permission_bounded_state_path() -> None:
    report = simulate_fdir_scenario()
    modes = [state["mode"] for state in report["states"]]
    assert modes == ["BOOT", "NOMINAL", "DEGRADED", "RECOVERY", "NOMINAL", "SAFE", "NOMINAL"]
    assert report["flight_software_claimed"] is False
    assert report["autonomous_safety_claimed"] is False


def test_fdir_rejects_invalid_resources_and_can_fail_critically() -> None:
    policy = FDIRPolicy()
    with pytest.raises(ValueError):
        fdir_transition(FDIRState(), policy, battery_soc=1.1)
    failed = fdir_transition(
        FDIRState(mode="NOMINAL"),
        policy,
        battery_soc=0.8,
        unrecoverable_critical_failure=True,
    )
    assert failed.mode == "FAILED"


def test_canonical_fault_tree_is_bounded() -> None:
    probability = canonical_fault_tree().probability()
    assert 0.0 < probability < 1.0


def test_r04_campaign_replays_exactly() -> None:
    first = simulate_r04_campaign(duration_days=180.0, start_offset=4096, count=256)
    second = simulate_r04_campaign(duration_days=180.0, start_offset=4096, count=256)
    assert first["failure_witness_digest"] == second["failure_witness_digest"]
    assert first["estimated_success_probability"] == second["estimated_success_probability"]
    assert first["flight_qualified_claimed"] is False


def test_r04_oakbench_passes_research_fixtures_only() -> None:
    report = run_r04_oak_benchmarks()
    assert report["passed"] is True
    assert len(report["checks"]) >= 7
    assert report["flight_qualified_claimed"] is False
    assert report["operational_reliability_claimed"] is False
    assert report["safety_certification_claimed"] is False
    assert report["autonomous_safety_claimed"] is False
