from __future__ import annotations

from dataclasses import asdict
import json

from .baselines import compare_baselines
from .bayes import BetaFunctionalPosterior, bayesian_route_preferences
from .calibration import ProbabilisticObservation, calibration_report
from .datasets import EUROSTAT_ENV_WASMUN, ingest_delimited_snapshot
from .flows import ConstrainedRecoveryOptimizer, FlowConstraints
from .lca import inventory_for_route
from .lcia import CharacterizationFactor, CharacterizationSet, characterize_inventory
from .models import Component, Material, RecoveryMode, RecoveryRoute
from .network import DemandNode, SupplyNode, TransferArc, min_cost_transport
from .oak import audit_plan
from .optimizer import Candidate, RecoveryOptimizer
from .provenance import ProvenanceRecord
from .scalable import BranchAndBoundRecoveryOptimizer, SearchBudget
from .scoring import ScoringPolicy, material_entropy
from .symbiosis import MaterialNeed, MaterialOffer
from .symbiosis_court import symbiosis_regret


def demo_problem() -> tuple[dict[str, Material], tuple[Candidate, ...]]:
    materials = {
        "copper": Material("copper", unit_value_per_kg=8.0, purity=0.98),
        "aluminium": Material("aluminium", unit_value_per_kg=2.4, purity=0.96),
        "polymer": Material("polymer", unit_value_per_kg=0.7, purity=0.90),
    }
    motor = Component(
        component_id="motor-01",
        name="electric motor",
        mass_kg=8.0,
        material_fractions={"copper": 0.22, "aluminium": 0.28, "polymer": 0.50},
        reuse_value=145.0,
        functional_probability=0.86,
        disassembly_cost=8.0,
        disassembly_energy_kwh=0.5,
        contamination=0.03,
        expected_future_cycles=2.0,
    )
    battery_module = Component(
        component_id="battery-01",
        name="battery module",
        mass_kg=12.0,
        material_fractions={"copper": 0.12, "aluminium": 0.38, "polymer": 0.50},
        reuse_value=90.0,
        functional_probability=0.35,
        hazardous=True,
        disassembly_cost=15.0,
        disassembly_energy_kwh=1.0,
        contamination=0.08,
        expected_future_cycles=1.0,
    )
    common_routes = (
        RecoveryRoute(RecoveryMode.REUSE, output_quality=0.95),
        RecoveryRoute(RecoveryMode.REPAIR, process_cost=18.0, energy_kwh=0.8, output_quality=0.92),
        RecoveryRoute(RecoveryMode.REMANUFACTURE, process_cost=30.0, energy_kwh=1.8, output_quality=0.96),
        RecoveryRoute(
            RecoveryMode.MATERIAL_RECYCLE,
            process_cost=6.0,
            energy_kwh=2.5,
            output_quality=0.82,
            retained_mass_fraction=0.88,
        ),
        RecoveryRoute(RecoveryMode.DISPOSAL, process_cost=2.0, retained_mass_fraction=0.0, output_quality=0.0),
    )
    hazardous_routes = tuple(
        RecoveryRoute(
            route.mode,
            process_cost=route.process_cost,
            energy_kwh=route.energy_kwh,
            risk=route.risk,
            externality_penalty=route.externality_penalty,
            output_quality=route.output_quality,
            retained_mass_fraction=route.retained_mass_fraction,
            requires_certified_process=route.mode is not RecoveryMode.DISPOSAL,
        )
        for route in common_routes
    )
    return materials, (Candidate(motor, common_routes), Candidate(battery_module, hazardous_routes))


def _r04_courts() -> dict:
    offers = (
        MaterialOffer("A1", "copper", 1, 1.0, 1.0),
        MaterialOffer("A2", "copper", 1, 1.0, 2.0),
    )
    needs = (
        MaterialNeed("B1", "copper", 1, 1.0, 2.0),
        MaterialNeed("B2", "copper", 1, 1.0, 1.5),
    )
    regret = symbiosis_regret(offers, needs)

    transport = min_cost_transport(
        (SupplyNode("s1", 1), SupplyNode("s2", 1)),
        (DemandNode("d1", 1), DemandNode("d2", 1)),
        (
            TransferArc("s1", "d1", 1, 1),
            TransferArc("s1", "d2", 1, 1),
            TransferArc("s2", "d1", 1, 2),
        ),
    )

    calibration = calibration_report(
        (
            ProbabilisticObservation(0.90, 1),
            ProbabilisticObservation(0.75, 1),
            ProbabilisticObservation(0.60, 0),
            ProbabilisticObservation(0.25, 0),
            ProbabilisticObservation(0.10, 0),
        ),
        bins=5,
    )

    public_text = "geo,year,value\nEU,2024,517\n"
    first_snapshot = ingest_delimited_snapshot(
        EUROSTAT_ENV_WASMUN,
        public_text,
        retrieved_at="2026-08-10T12:00:00-04:00",
    )
    second_snapshot = ingest_delimited_snapshot(
        EUROSTAT_ENV_WASMUN,
        public_text,
        retrieved_at="2026-08-10T12:00:00-04:00",
    )

    materials, candidates = demo_problem()
    inventory = inventory_for_route(candidates[0].component, candidates[0].routes[0])
    synthetic_provenance = ProvenanceRecord(
        "synthetic-lcia-factors",
        "https://example.invalid/synthetic-lcia-factors",
        "2026-08-10",
        "0" * 64,
    )
    factor_set = CharacterizationSet(
        name="synthetic-benchmark-only",
        version="1",
        methodology="synthetic-test",
        provenance=synthetic_provenance,
        factors=(CharacterizationFactor("electricity", "kWh", "climate", 0.5, "kgCO2e", "input"),),
    )
    characterization = characterize_inventory(inventory, factor_set)

    return {
        "symbiosis": {
            "greedy_quantity_kg": regret.greedy_quantity_kg,
            "exact_quantity_kg": regret.exact_quantity_kg,
            "quantity_regret_kg": regret.quantity_regret_kg,
            "quantity_regret_detected": regret.quantity_regret_kg > 0,
            "cost_regret_comparable": regret.comparable_cost_regret is not None,
        },
        "transport": {
            "total_flow": transport.total_flow,
            "total_cost": transport.total_cost,
            "optimality_certified": transport.optimality_certified,
            "unmet_demand": transport.unmet_demand,
        },
        "calibration": {
            "brier_score": round(calibration.brier_score, 6),
            "log_loss": round(calibration.log_loss, 6),
            "ece": round(calibration.expected_calibration_error, 6),
            "claim_boundary": calibration.claim_boundary,
        },
        "dataset_snapshot": {
            "source_id": first_snapshot.provenance.source_id,
            "sha256": first_snapshot.provenance.sha256,
            "hash_reproducible": first_snapshot.provenance.sha256 == second_snapshot.provenance.sha256,
            "claim_boundary": first_snapshot.claim_boundary,
        },
        "lcia": {
            "matched_flows": characterization.matched_flows,
            "unmatched_flows": list(characterization.unmatched_flows),
            "claim_boundary": characterization.claim_boundary,
            "certified_lca": False,
        },
    }


def run_oakbench() -> dict:
    materials, candidates = demo_problem()
    policy = ScoringPolicy(
        energy_shadow_price_per_kwh=0.18,
        risk_penalty=25.0,
        preservation_bonus=1.0,
        future_cycle_weight=0.7,
    )
    plan = RecoveryOptimizer(materials, policy).optimize(candidates)
    report = audit_plan(plan)

    constraints = FlowConstraints(max_process_cost=1_000.0, max_energy_kwh=100.0, max_risk_sum=2.0)
    exact = ConstrainedRecoveryOptimizer(materials, policy).optimize(candidates, constraints)
    scalable = BranchAndBoundRecoveryOptimizer(materials, policy).optimize(
        candidates,
        constraints,
        budget=SearchBudget(max_nodes=10_000),
    )
    baselines = compare_baselines(candidates, materials, policy)

    posterior = BetaFunctionalPosterior().updated(successes=8, failures=2)
    bayes_summary = bayesian_route_preferences(
        candidates[0].component,
        materials,
        candidates[0].routes,
        posterior,
        draws=512,
        seed=7,
        policy=policy,
    )
    lca_inventory = inventory_for_route(candidates[0].component, candidates[0].routes[0])

    return {
        "bench_version": "0.4.0",
        "deterministic": True,
        "compatibility": {"r03_contract_preserved": True},
        "capabilities": [
            "resource_graph",
            "material_passport",
            "route_optimization",
            "small_coupled_flow_oracle",
            "branch_and_bound_solver",
            "baseline_ablations",
            "bayesian_uncertainty",
            "probability_calibration_metrics",
            "lca_inventory_interface",
            "external_lcia_adapter",
            "industrial_symbiosis",
            "exact_symbiosis_regret_court",
            "capacity_transport_min_cost_flow",
            "urban_mine",
            "provenance_hashing",
            "public_dataset_snapshot_ingestion",
        ],
        "plan": {
            "total_score": round(plan.total_score, 6),
            "recovered_value": round(plan.recovered_value, 6),
            "retained_mass_kg": round(plan.retained_mass_kg, 6),
            "dry_run_only": plan.dry_run_only,
            "evaluations": [
                {
                    "component_id": item.component_id,
                    "mode": item.mode.value,
                    "score": round(item.score, 6),
                    "recovered_value": round(item.recovered_value, 6),
                    "total_cost": round(item.total_cost, 6),
                    "retained_mass_kg": round(item.retained_mass_kg, 6),
                    "dry_run_only": item.dry_run_only,
                    "warnings": list(item.warnings),
                }
                for item in plan.evaluations
            ],
        },
        "solver_crosscheck": {
            "exact_total_score": round(exact.plan.total_score, 6),
            "scalable_total_score": round(scalable.plan.total_score, 6),
            "modes_equal": exact.plan.modes() == scalable.plan.modes(),
            "score_equal": abs(exact.plan.total_score - scalable.plan.total_score) <= 1e-9,
            "optimality_certified": scalable.optimality_certified,
            "evaluated_nodes": scalable.evaluated_nodes,
            "exhaustive_combinations": exact.evaluated_combinations,
            "pruned_by_bound": scalable.pruned_by_bound,
            "pruned_by_constraints": scalable.pruned_by_constraints,
        },
        "baselines": {
            baseline.name: {
                "total_score_under_its_rule": round(baseline.plan.total_score, 6),
                "modes": baseline.plan.modes(),
            }
            for baseline in baselines
        },
        "bayes": {
            "posterior_mean_functional_probability": round(posterior.mean, 6),
            "route_preferences": [
                {
                    "mode": item.mode,
                    "win_probability": round(item.win_probability, 6),
                    "mean_score": round(item.mean_score, 6),
                    "score_std": round(item.score_std, 6),
                }
                for item in bayes_summary
            ],
        },
        "lca_inventory": lca_inventory.to_dict(),
        "r04_courts": _r04_courts(),
        "component_entropy": {
            candidate.component.component_id: round(material_entropy(candidate.component), 6)
            for candidate in candidates
        },
        "oak": asdict(report),
        "limits": [
            "synthetic decision benchmark only",
            "branch-and-bound remains exponential in the worst case",
            "transport court certifies only the declared bipartite min-cost flow problem",
            "Bayesian posterior remains a model until calibrated on observations",
            "calibration metrics do not establish causality or safety",
            "public source catalog and snapshot hashing do not validate source semantics",
            "LCIA adapter uses externally supplied factors and does not certify lifecycle conclusions",
            "no physical processing authorization",
        ],
    }


def render_oakbench() -> str:
    return json.dumps(run_oakbench(), indent=2, sort_keys=True)
