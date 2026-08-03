from __future__ import annotations

from dataclasses import replace
from math import pi, sqrt

import pytest

from omega_space_hg_t import (
    EARTH_MU_M3_S2,
    EARTH_RADIUS_M,
    SpaceHyperedge,
    SpaceHypergraph,
    SpaceNode,
    UnboundedDesignFrontier,
    canonical_6u_mission,
    circular_orbit_state,
    mission_from_dict,
    optimize_designs,
    orbital_period_s,
    propagate_two_body,
    relative_energy_drift,
    run_oak_benchmarks,
    simulate_mission,
)


def test_circular_orbit_period_matches_closed_form() -> None:
    radius = EARTH_RADIUS_M + 550_000.0
    state = circular_orbit_state(radius, EARTH_MU_M3_S2)
    expected = 2.0 * pi * sqrt(radius**3 / EARTH_MU_M3_S2)
    assert orbital_period_s(state, EARTH_MU_M3_S2) == pytest.approx(expected, rel=1e-14)


def test_symplectic_propagation_limits_energy_drift() -> None:
    config = canonical_6u_mission(duration_orbits=1.0, step_s=20.0)
    states = propagate_two_body(
        config.orbit,
        config.duration_s,
        config.step_s,
        config.central_body_mu_m3_s2,
    )
    assert relative_energy_drift(states, config.central_body_mu_m3_s2) < 2e-4


def test_hypergraph_rejects_unknown_members_and_reports_neighbors() -> None:
    graph = SpaceHypergraph("test")
    graph.add_node(SpaceNode("mission", "mission"))
    graph.add_node(SpaceNode("power", "power"))
    graph.add_edge(SpaceHyperedge("flow", "energy", ("mission", "power")))
    assert graph.neighbors("mission") == ("power",)
    assert graph.validate()["valid"] is True
    with pytest.raises(ValueError):
        graph.add_edge(SpaceHyperedge("invalid", "flow", ("mission", "missing")))


def test_manifest_round_trip_preserves_canonical_configuration() -> None:
    config = canonical_6u_mission()
    replay = mission_from_dict(config.to_dict())
    assert replay.to_dict() == config.to_dict()


def test_coupled_mission_is_deterministic_and_traceable() -> None:
    config = canonical_6u_mission(duration_orbits=1.0, step_s=30.0)
    first = simulate_mission(config)
    second = simulate_mission(config)
    assert first.metrics == second.metrics
    assert first.hypergraph["validation"]["valid"] is True
    assert first.metrics.minimum_battery_fraction > 0.10
    assert first.metrics.maximum_stored_data_fraction < 0.98
    assert first.config.flight_qualified_claimed is False


def test_invalid_claim_boundary_is_rejected() -> None:
    config = canonical_6u_mission()
    with pytest.raises(ValueError):
        replace(config, flight_qualified_claimed=True).validate()


def test_unbounded_frontier_is_replayable_without_fixed_cap() -> None:
    frontier = UnboundedDesignFrontier()
    assert frontier.permanent_total_cap is None
    assert frontier.decode(10**12 + 17) == frontier.decode(10**12 + 17)
    plan = frontier.plan(1024, 16)
    assert plan["next_offset"] == 1040
    assert len(plan["addresses"]) == 16


def test_optimizer_returns_complete_evaluations_and_pareto_set() -> None:
    config = canonical_6u_mission(duration_orbits=0.25, step_s=60.0)
    report = optimize_designs(config, start_offset=5, count=8)
    assert report["frontier"]["permanent_total_cap"] is None
    assert len(report["evaluations"]) == 8
    assert 1 <= report["pareto_count"] <= 8
    assert report["flight_qualified_claimed"] is False


def test_oakbench_passes_software_fixtures_only() -> None:
    report = run_oak_benchmarks()
    assert report["passed"] is True
    assert report["theorem_claimed"] is False
    assert report["flight_qualified_claimed"] is False
    assert report["scientific_validation_claimed"] is False
    assert len(report["checks"]) >= 6
