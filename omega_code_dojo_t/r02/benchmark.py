from __future__ import annotations

from .campaign import CampaignEngine
from .frontier import DEFAULT_FRONTIER
from .hashing import sha256_hex
from .models import CampaignPolicy, ProvenanceRecord
from .mutation import MutationOperator, MutationRegistry


def fixture_provenance() -> ProvenanceRecord:
    return ProvenanceRecord(
        source_id="omega-original-r02-fixtures",
        source_type="omega_original",
        author="Tristan-TM-Poly",
        license_id="MIT",
        content_hash=sha256_hex("omega-code-dojo-r02-original-fixtures"),
        retrieved_at="2026-08-03T00:00:00Z",
        training_allowed=True,
        redistribution_allowed=True,
        commercial_use_allowed=True,
        attribution_required=True,
        notes=("Original Ω-CODE-DOJO-T∞ R0.2 software fixtures.",),
    )


def blocked_provenance() -> ProvenanceRecord:
    return ProvenanceRecord(
        source_id="blocked-scrape-fixture",
        source_type="scraped_restricted_service",
        author="unknown",
        license_id="UNKNOWN",
        content_hash=sha256_hex("blocked-scrape-fixture"),
        retrieved_at="2026-08-03T00:00:00Z",
        training_allowed=True,
        redistribution_allowed=True,
        commercial_use_allowed=True,
    )


def run_r02_benchmark(materialization_budget: int = 32) -> dict[str, object]:
    policy = CampaignPolicy(
        materialization_budget=materialization_budget,
        permanent_cap=None,
        novelty_plateau_window=8,
        novelty_plateau_threshold=0.0,
    )
    fixture_mutations = MutationRegistry(
        MutationOperator(
            operator_id=f"mut.fixture.{family}",
            family=family,
            description=f"Deterministic OAK fixture for {family}.",
            semantic_risk="fixture",
            expected_countercheck=f"fixture-counterexample:{family}",
        )
        for family in DEFAULT_FRONTIER.mutation_families.values
    )
    first = CampaignEngine(mutations=fixture_mutations).run(policy, fixture_provenance())
    second = CampaignEngine(mutations=fixture_mutations).run(policy, fixture_provenance())
    blocked = CampaignEngine().run(policy, blocked_provenance())

    first_payload = first.to_dict()
    second_payload = second.to_dict()
    deterministic = first_payload == second_payload
    mutation_scores = [item.mutation_score for item in first.observations]
    pass_rate = (
        sum(item.success for item in first.observations) / len(first.observations)
        if first.observations
        else 0.0
    )
    mean_mutation_score = (
        sum(mutation_scores) / len(mutation_scores) if mutation_scores else 0.0
    )

    invariants = {
        "logical_frontier_is_3221225472": (
            DEFAULT_FRONTIER.logical_cell_count == 3_221_225_472
        ),
        "deterministic_receipt": deterministic,
        "budget_materialized": first.materialized_cells == materialization_budget,
        "no_permanent_cap": first.permanent_total_cap is None,
        "all_fixture_tasks_supported": pass_rate == 1.0,
        "all_seed_mutants_rejected": mean_mutation_score == 1.0,
        "blocked_source_materializes_nothing": blocked.materialized_cells == 0,
        "blocked_source_hits_safety_gate": blocked.stop_reason.value == "safety_gate",
        "no_neural_training_claim": first.claims["neural_training_claimed"] is False,
        "no_codewars_affiliation_claim": (
            first.claims["codewars_affiliation_claimed"] is False
        ),
    }
    certified = all(invariants.values())
    return {
        "status": (
            "CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"
            if certified
            else "OAK_INVARIANT_FAILURE_R0_2"
        ),
        "system": "omega-code-dojo-t-infinity",
        "version": "R0.2",
        "logical_frontier_cells": DEFAULT_FRONTIER.logical_cell_count,
        "axis_cardinalities": DEFAULT_FRONTIER.axis_cardinalities(),
        "materialized_cells": first.materialized_cells,
        "allocated_units": first.allocated_units,
        "permanent_total_cap": first.permanent_total_cap,
        "pass_rate": pass_rate,
        "mean_mutation_score": mean_mutation_score,
        "deterministic": deterministic,
        "receipt_sha256": first.receipt_sha256,
        "blocked_receipt_sha256": blocked.receipt_sha256,
        "invariants": invariants,
        "claims": first.claims,
        "receipt": first_payload,
        "blocked_receipt": blocked.to_dict(),
    }
