"""OAK falsification gates for Ω-SPACE-HG-T∞ R0.1."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Callable

from .hypergraph import build_spacecraft_hypergraph
from .mission import simulate_mission
from .models import MissionConfig, OrbitState, SpacecraftConfig
from .optimization import UnboundedDesignFrontier
from .orbit import orbital_period_s, propagate_two_body, relative_energy_drift


EARTH_MU_M3_S2 = 3.986004418e14
EARTH_RADIUS_M = 6_378_137.0


@dataclass(frozen=True)
class OAKCheck:
    name: str
    passed: bool
    observed: Any
    criterion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_6u_mission(duration_orbits: float = 2.0, step_s: float = 20.0) -> MissionConfig:
    radius_m = EARTH_RADIUS_M + 550_000.0
    speed_m_s = sqrt(EARTH_MU_M3_S2 / radius_m)
    orbit = OrbitState((radius_m, 0.0, 0.0), (0.0, speed_m_s, 0.0))
    spacecraft = SpacecraftConfig(
        name="Omega-6U-Observer",
        dry_mass_kg=8.0,
        payload_mass_kg=2.0,
        panel_area_m2=0.32,
        panel_efficiency=0.29,
        battery_capacity_wh=260.0,
        initial_battery_fraction=0.82,
        base_load_w=18.0,
        payload_load_w=32.0,
        downlink_load_w=38.0,
        radiator_area_m2=0.12,
        absorptivity=0.35,
        emissivity=0.80,
        thermal_capacity_j_k=40_000.0,
        initial_temperature_k=293.15,
        data_generation_mbps=8.0,
        storage_capacity_gb=128.0,
        downlink_rate_mbps=80.0,
    )
    period_s = orbital_period_s(orbit, EARTH_MU_M3_S2)
    return MissionConfig(
        mission_id="omega-space-6u-observer-r01",
        objective="Demonstrate traceable LEO observation mission co-simulation",
        duration_s=duration_orbits * period_s,
        step_s=step_s,
        central_body_mu_m3_s2=EARTH_MU_M3_S2,
        central_body_radius_m=EARTH_RADIUS_M,
        orbit=orbit,
        spacecraft=spacecraft,
        payload_duty_cycle=0.24,
        downlink_duty_cycle=0.14,
        eclipse_fraction=0.36,
        metadata={
            "status": "research-software-fixture",
            "baseline_targets": ["GMAT", "Orekit", "Basilisk"],
        },
    )


def _capture(name: str, criterion: str, function: Callable[[], tuple[bool, Any]]) -> OAKCheck:
    try:
        passed, observed = function()
        return OAKCheck(name, bool(passed), observed, criterion)
    except Exception as error:  # OAK reports failures instead of hiding them.
        return OAKCheck(name, False, f"{type(error).__name__}: {error}", criterion)


def run_oak_benchmarks() -> dict[str, Any]:
    config = canonical_6u_mission()

    def orbit_check() -> tuple[bool, Any]:
        period = orbital_period_s(config.orbit, config.central_body_mu_m3_s2)
        states = propagate_two_body(config.orbit, period, config.step_s, config.central_body_mu_m3_s2)
        drift = relative_energy_drift(states, config.central_body_mu_m3_s2)
        return drift < 2e-4, drift

    def hypergraph_check() -> tuple[bool, Any]:
        graph = build_spacecraft_hypergraph(
            "oak-fixture",
            ("payload", "power", "thermal", "communications", "flight_software"),
            ("trace every requirement",),
        ).to_dict()
        validation = graph["validation"]
        return bool(validation["valid"]), validation

    def mission_check() -> tuple[bool, Any]:
        result = simulate_mission(config)
        metrics = result.metrics.to_dict()
        passed = (
            metrics["minimum_battery_fraction"] > 0.10
            and metrics["maximum_stored_data_fraction"] < 0.98
            and metrics["energy_drift_fraction"] < 2e-4
        )
        return passed, metrics

    def determinism_check() -> tuple[bool, Any]:
        first = simulate_mission(config).metrics.to_dict()
        second = simulate_mission(config).metrics.to_dict()
        return first == second, first

    def frontier_check() -> tuple[bool, Any]:
        frontier = UnboundedDesignFrontier()
        address = frontier.decode(10**9 + 7).to_dict()
        replay = frontier.decode(10**9 + 7).to_dict()
        return frontier.permanent_total_cap is None and address == replay, address

    def claim_boundary_check() -> tuple[bool, Any]:
        boundaries = {
            "theorem_claimed": config.theorem_claimed,
            "flight_qualified_claimed": config.flight_qualified_claimed,
            "scientific_validation_claimed": config.scientific_validation_claimed,
        }
        return not any(boundaries.values()), boundaries

    checks = (
        _capture("two_body_energy_drift", "relative drift < 2e-4 over one orbit", orbit_check),
        _capture("hypergraph_integrity", "no orphan nodes and at least one edge", hypergraph_check),
        _capture("coupled_mission_budget", "energy, storage and orbit gates pass", mission_check),
        _capture("deterministic_replay", "identical inputs produce identical metrics", determinism_check),
        _capture("unbounded_frontier_replay", "no permanent cap and exact address replay", frontier_check),
        _capture("claim_boundaries", "no proof, qualification or scientific-validation claim", claim_boundary_check),
    )
    passed = all(check.passed for check in checks)
    return {
        "suite": "OMEGA-SPACE-HG-T-R0.1-OAKBench",
        "passed": passed,
        "checks": [check.to_dict() for check in checks],
        "theorem_claimed": False,
        "flight_qualified_claimed": False,
        "scientific_validation_claimed": False,
        "limitations": [
            "two-body orbit only",
            "single reduced thermal node",
            "deterministic duty-cycle operations",
            "mass is an early-design proxy",
            "no hardware, HIL, environmental or flight qualification",
        ],
    }
