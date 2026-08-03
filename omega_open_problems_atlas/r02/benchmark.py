"""Deterministic R0.2 benchmark and large finite fixture.

The generated records are synthetic research-software fixtures. They are never
counted as independently verified open problems and never claim solutions.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile

from .campaign import allocate_campaign, campaign_manifest
from .competition import competition_count, research_open_count
from .dedupe import exact_duplicate_groups, near_duplicate_findings
from .merkle import inclusion_proof, merkle_root, verify_inclusion
from .models import LeadStatus, MethodCard, ProblemLead
from .obligations import OBLIGATION_OPERATORS, stream_obligations
from .store import AtlasStore
from .transfer import candidate_transfers, compile_transfer_edges, transfer_summary


DOMAINS_64: tuple[str, ...] = (
    "algebra", "algebraic_geometry", "algebraic_number_theory", "analytic_number_theory",
    "analysis", "arithmetic_geometry", "category_theory", "coding_theory",
    "combinatorial_geometry", "combinatorics", "commutative_algebra", "complex_analysis",
    "computability", "convex_geometry", "differential_geometry", "dynamical_systems",
    "ergodic_theory", "extremal_combinatorics", "finite_geometry", "fluid_mechanics",
    "functional_analysis", "geometric_group_theory", "graph_theory", "harmonic_analysis",
    "homological_algebra", "information_theory", "knot_theory", "lie_theory",
    "logic", "mathematical_biology", "mathematical_economics", "mathematical_physics",
    "metric_geometry", "model_theory", "noncommutative_geometry", "number_theory",
    "numerical_analysis", "operator_algebras", "optimization", "partial_differential_equations",
    "probability", "proof_theory", "quantum_information", "representation_theory",
    "set_theory", "spectral_theory", "statistics", "stochastic_processes",
    "symplectic_geometry", "theoretical_computer_science", "topological_dynamics", "topology",
    "transcendence_theory", "tropical_geometry", "additive_combinatorics", "approximation_theory",
    "automata_theory", "calculus_of_variations", "discrete_geometry", "game_theory",
    "inverse_problems", "mathematical_chemistry", "random_matrix_theory", "scientific_computing",
)

METHOD_FAMILIES: tuple[str, ...] = (
    "algebraic", "analytic", "categorical", "combinatorial", "computational", "geometric",
    "logical", "probabilistic", "spectral", "topological", "variational", "formal",
    "adversarial", "asymptotic", "optimization", "statistical",
)

RESULT_CLASSES: tuple[str, ...] = (
    "existence", "nonexistence", "uniqueness", "classification", "upper_bound", "lower_bound",
    "asymptotic", "equivalence", "algorithm", "complexity", "construction", "counterexample",
    "regularity", "stability", "rigidity", "universality", "density", "distribution",
    "decidability", "independence", "formalization", "reconstruction", "approximation", "optimization",
    "convergence", "divergence", "compactness", "extension", "embedding", "factorization",
    "enumeration", "representation",
)

EVIDENCE_MODES: tuple[str, ...] = (
    "source", "literature", "symbolic", "exact", "interval", "numerical", "formal", "proof_kernel",
    "independent_reproduction", "peer_review", "negative_control", "ablation", "counterexample",
    "benchmark", "citation_audit", "license_audit",
)


def method_bank(count: int = 128) -> tuple[MethodCard, ...]:
    methods: list[MethodCard] = []
    for index in range(count):
        family = METHOD_FAMILIES[index % len(METHOD_FAMILIES)]
        domain_a = DOMAINS_64[index % len(DOMAINS_64)]
        domain_b = DOMAINS_64[(index * 7 + 11) % len(DOMAINS_64)]
        methods.append(
            MethodCard(
                method_id=f"OPA-METHOD-{index:04d}",
                name=f"{family} research method {index:04d}",
                family=family,
                domains=tuple(sorted({domain_a, domain_b})),
                prerequisites=(f"declared definitions for {domain_a}", "source provenance"),
                known_failure_modes=(
                    "method analogy mistaken for proof",
                    "untracked assumption introduced during transfer",
                ),
                implementation_refs=(f"fixture://method/{index:04d}",),
                status="SYNTHETIC_METHOD_FIXTURE",
            )
        )
    return tuple(methods)


def synthetic_leads(count: int) -> tuple[ProblemLead, ...]:
    leads: list[ProblemLead] = []
    for index in range(count):
        domain_a = DOMAINS_64[index % len(DOMAINS_64)]
        domain_b = DOMAINS_64[(index * 13 + 5) % len(DOMAINS_64)]
        method_a = f"OPA-METHOD-{index % 128:04d}"
        method_b = f"OPA-METHOD-{(index * 3 + 17) % 128:04d}"
        kind = "COMPETITION_PROBLEM" if index % 31 == 0 else "RESEARCH_PROBLEM"
        leads.append(
            ProblemLead(
                lead_id=f"OPA-SYN-{index:08d}",
                source_id="SYNTHETIC_R02_FIXTURE",
                source_locator=f"fixture://problem/{index:08d}",
                title=f"Synthetic research lead {index:08d}",
                statement_summary=(
                    f"Fixture statement {index:08d}: investigate a declared {RESULT_CLASSES[index % len(RESULT_CLASSES)]} "
                    f"property coupling {domain_a} and {domain_b}. This is not a real open-problem claim."
                ),
                domains=tuple(sorted({domain_a, domain_b})),
                kind=kind,
                lead_status=LeadStatus.SOURCE_REPORTED,
                methods=tuple(sorted({method_a, method_b})),
                license_reviewed=True,
                literature_search_required=True,
                independently_checked_open=False,
                finite_computation_is_not_proof=True,
                solution_claimed=False,
                metadata={
                    "generated_fixture": True,
                    "impact": 0.35 + (index % 11) / 20,
                    "testability": 0.40 + (index % 7) / 14,
                    "formalizability": 0.30 + (index % 5) / 10,
                    "difficulty": 0.60 + (index % 9) / 18,
                    "maintenance_cost": 0.40 + (index % 3) / 10,
                },
            )
        )
    return tuple(leads)


def logical_frontier_count(method_count: int = 128) -> int:
    return (
        len(DOMAINS_64)
        * len(OBLIGATION_OPERATORS)
        * method_count
        * len(RESULT_CLASSES)
        * len(EVIDENCE_MODES)
    )


def run_benchmark(
    *,
    lead_count: int = 4096,
    obligation_budget: int = 100_000,
    transfer_lead_sample: int = 256,
    sqlite_path: str | Path | None = None,
) -> dict[str, object]:
    if lead_count <= 0:
        raise ValueError("lead_count must be positive")
    if obligation_budget < 0:
        raise ValueError("obligation_budget must be non-negative")
    leads = synthetic_leads(lead_count)
    methods = method_bank()
    campaign_obligations = tuple(
        stream_obligations(leads, min(8192, obligation_budget))
    )
    allocations = allocate_campaign(
        leads,
        campaign_obligations,
        min(10_001, obligation_budget),
    ) if obligation_budget else ()
    candidates = candidate_transfers(
        leads[: min(transfer_lead_sample, len(leads))],
        methods[:32],
        threshold=0.20,
        max_pairs_per_method=64,
    )
    edges = compile_transfer_edges(candidates)

    temporary: tempfile.TemporaryDirectory[str] | None = None
    if sqlite_path is None:
        temporary = tempfile.TemporaryDirectory(prefix="opa-r02-")
        sqlite_path = Path(temporary.name) / "atlas.sqlite3"
    sqlite_path = Path(sqlite_path)
    with AtlasStore(sqlite_path) as store:
        store.insert_leads(leads)
        with store.transaction():
            for method in methods:
                store.upsert_method(method)
            for edge in edges:
                store.upsert_edge(edge)
        store.insert_obligations(stream_obligations(leads, obligation_budget))
        checkpoint = store.checkpoint("OPA-R02-BENCHMARK", "2026-08-03T00:00:00Z")
        counts = {
            "leads": store.count("leads"),
            "methods": store.count("methods"),
            "obligations": store.count("obligations"),
            "transfer_edges": store.count("transfer_edges"),
            "independently_checked_open": store.independently_checked_open_count(),
            "solution_claims": store.solution_claim_count(),
        }
        hashes = store.hashes()
    if temporary is not None:
        temporary.cleanup()

    exact_duplicates = exact_duplicate_groups(leads)
    near_duplicates = near_duplicate_findings(leads[: min(512, len(leads))], threshold=0.90)
    proof_index = len(hashes) // 2
    proof = inclusion_proof(hashes, proof_index) if hashes else ()
    root = merkle_root(hashes)
    report = {
        "system": "OMEGA-OPEN-PROBLEMS-ATLAS-T-INFINITY",
        "version": "R0.2-MAX",
        "status": "CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2",
        "logical_frontier_count": logical_frontier_count(len(methods)),
        "logical_frontier_materialized": False,
        "materialized_fixture": {
            "lead_count": lead_count,
            "obligation_budget": obligation_budget,
            "method_count": len(methods),
            "transfer_lead_sample": min(transfer_lead_sample, len(leads)),
        },
        "counts": counts,
        "checkpoint": checkpoint,
        "campaign": campaign_manifest(allocations),
        "transfer": transfer_summary(edges),
        "dedupe": {
            "exact_duplicate_group_count": len(exact_duplicates),
            "near_duplicate_finding_count": len(near_duplicates),
        },
        "separation": {
            "research_open_count": research_open_count(leads),
            "competition_count": competition_count(leads),
            "generated_fixture_count": len(leads),
        },
        "merkle": {
            "leaf_count": len(hashes),
            "root": root,
            "sample_index": proof_index,
            "sample_proof_length": len(proof),
            "sample_proof_valid": bool(hashes) and verify_inclusion(hashes[proof_index], proof, root),
        },
        "permanent_total_cap": None,
        "priority_score_is_not_truth_probability": True,
        "generated_fixture_is_not_open_problem": True,
        "finite_computation_is_not_proof": True,
        "formal_skeleton_is_not_completed_proof": True,
        "solution_claimed": False,
        "scientific_validation_claimed": False,
        "competition_participation_claimed": False,
        "automated_submission_performed": False,
    }
    canonical = json.dumps(report, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    report["report_sha256"] = sha256(canonical).hexdigest()
    return report


def write_report(report: dict[str, object], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
