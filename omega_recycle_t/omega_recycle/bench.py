from __future__ import annotations

from dataclasses import asdict
import json

from .baselines import compare_baselines
from .bayes import BetaFunctionalPosterior, bayesian_route_preferences
from .flows import ConstrainedRecoveryOptimizer, FlowConstraints
from .lca import inventory_for_route
from .models import Component, Material, RecoveryMode, RecoveryRoute
from .oak import audit_plan
from .optimizer import Candidate, RecoveryOptimizer
from .scalable import BranchAndBoundRecoveryOptimizer, SearchBudget
from .scoring import ScoringPolicy, material_entropy


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
        "bench_version": "0.3.0",
        "deterministic": True,
        "capabilities": [
            "resource_graph",
            "material_passport",
            "route_optimization",
            "small_coupled_flow_oracle",
            "branch_and_bound_solver",
            "baseline_ablations",
            "bayesian_uncertainty",
            "lca_inventory_interface",
            "industrial_symbiosis",
            "urban_mine",
            "provenance_hashing",
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
        "component_entropy": {
            candidate.component.component_id: round(material_entropy(candidate.component), 6)
            for candidate in candidates
        },
        "oak": asdict(report),
        "limits": [
            "synthetic benchmark only",
            "branch-and-bound remains exponential in the worst case",
            "Bayesian posterior is model-level and not empirically calibrated",
            "LCA interface is inventory-only and performs no impact assessment",
            "no physical processing authorization",
        ],
    }


def render_oakbench() -> str:
    return json.dumps(run_oakbench(), indent=2, sort_keys=True)
