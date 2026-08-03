from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

from .analyzer import LearningAnalyzer
from .hashing import sha256_hex
from .ledger import LearningLedger
from .planner import LearningPlanner


def fixture_receipts() -> tuple[dict[str, Any], ...]:
    logical = 3_221_225_472
    campaigns = []
    rows = [
        (
            "campaign.learning.001",
            [
                _obs("arrays", "window", "python", "off_by_one", True, 1.0, 1.0, 0.72, 3),
                _obs("arrays", "window", "rust", "off_by_one", True, 1.0, 1.0, 0.68, 4),
                _obs("graphs", "shortest_path", "python", "wrong_update", False, 1.0, 0.5, 0.81, 4, ("relaxation_order",)),
                _obs("strings", "normalization", "javascript", "unicode", False, 1.0, 0.25, 0.89, 3, ("unicode_combining_mark",)),
                _obs("arrays", "partition", "cpp", "boundary", False, 1.0, 0.5, 0.74, 2, ("empty_partition", "off_by_one")),
                _obs("dynamic_programming", "sequence", "python", "wrong_base", True, 1.0, 1.0, 0.61, 5),
            ],
        ),
        (
            "campaign.learning.002",
            [
                _obs("graphs", "shortest_path", "rust", "wrong_update", False, 1.0, 0.5, 0.84, 5, ("relaxation_order",)),
                _obs("strings", "normalization", "python", "unicode", False, 1.0, 0.25, 0.91, 3, ("unicode_combining_mark",)),
                _obs("arrays", "partition", "rust", "boundary", False, 1.0, 0.5, 0.79, 2, ("empty_partition", "off_by_one")),
                _obs("arrays", "window", "cpp", "off_by_one", True, 1.0, 1.0, 0.70, 3),
                _obs("dynamic_programming", "sequence", "rust", "wrong_base", True, 1.0, 1.0, 0.67, 5),
                _obs("graphs", "traversal", "python", "visited_timing", True, 1.0, 1.0, 0.58, 4),
            ],
        ),
        (
            "campaign.learning.003",
            [
                _obs("graphs", "shortest_path", "cpp", "wrong_update", True, 0.0, 1.0, 0.18, 8),
                _obs("strings", "normalization", "rust", "unicode", False, 0.0, 0.25, 0.09, 8, ("unicode_combining_mark",)),
                _obs("arrays", "partition", "python", "boundary", False, 0.0, 0.5, 0.08, 7, ("empty_partition", "off_by_one")),
                _obs("arrays", "window", "javascript", "off_by_one", True, 0.0, 1.0, 0.07, 7),
                _obs("dynamic_programming", "sequence", "cpp", "wrong_base", True, 0.0, 1.0, 0.06, 8),
                _obs("graphs", "traversal", "rust", "visited_timing", True, 0.0, 1.0, 0.05, 8),
                _obs("sorting", "comparison", "python", "stability", True, 0.0, 1.0, 0.04, 9),
                _obs("sorting", "comparison", "rust", "stability", True, 0.0, 1.0, 0.03, 9),
            ],
        ),
    ]
    for campaign_id, observations in rows:
        payload = {
            "campaign_id": campaign_id,
            "system_version": "R0.2-fixture",
            "logical_frontier_cells": logical,
            "observations": observations,
        }
        payload["receipt_sha256"] = sha256_hex(payload)
        campaigns.append(payload)
    return tuple(campaigns)


def _obs(
    domain: str,
    archetype: str,
    language: str,
    mutation_family: str,
    success: bool,
    novelty: float,
    mutation_score: float,
    information_gain: float,
    cost_units: int,
    failure_signatures: tuple[str, ...] = (),
) -> dict[str, Any]:
    difficulty = "band-12"
    regime = "deterministic"
    address = "/".join(
        (domain, archetype, difficulty, language, regime, mutation_family)
    )
    return {
        "cell": {
            "domain": domain,
            "archetype": archetype,
            "difficulty_band": difficulty,
            "language": language,
            "execution_regime": regime,
            "mutation_family": mutation_family,
            "address": address,
        },
        "task_id": f"task.{sha256_hex(address)[:16]}",
        "success": success,
        "novelty": novelty,
        "mutation_score": mutation_score,
        "information_gain": information_gain,
        "cost_units": cost_units,
        "evidence_status": "supported" if success else "falsified",
        "failure_signatures": list(failure_signatures),
    }


def run_r03_benchmark() -> dict[str, Any]:
    receipts = fixture_receipts()
    analyzer = LearningAnalyzer()
    first = analyzer.analyze(receipts, plateau_window=8)
    second = analyzer.analyze(deepcopy(receipts), plateau_window=8)
    planner = LearningPlanner()
    first_plan = planner.plan(first)
    second_plan = planner.plan(second)

    ledger = LearningLedger()
    entry = ledger.append(first)
    reports = {first.report_id: first}
    ledger_valid = ledger.verify(reports)
    tampered = replace(first, total_cost_units=first.total_cost_units + 1)
    tamper_detected = not ledger.verify({first.report_id: tampered})

    insight_kinds = {item.kind.value for item in first.insights}
    action_kinds = {item.kind.value for item in first_plan}
    top_cluster = first.failure_clusters[0] if first.failure_clusters else None
    invariants = {
        "deterministic_report": first.to_dict() == second.to_dict(),
        "deterministic_plan": (
            [item.to_dict() for item in first_plan]
            == [item.to_dict() for item in second_plan]
        ),
        "report_hash_present": len(first.report_sha256) == 64,
        "ledger_valid": ledger_valid,
        "ledger_detects_tampering": tamper_detected,
        "counterexample_insight_present": "counterexample" in insight_kinds,
        "test_gap_insight_present": "test_gap" in insight_kinds,
        "transfer_insight_present": "transfer" in insight_kinds,
        "plateau_detected": first.plateau.detected,
        "repair_action_present": (
            "repair_test" in action_kinds or "repair_skill" in action_kinds
        ),
        "frontier_coverage_explicit": first.coverage_ratio > 0.0,
        "no_causal_transfer_claim": first.claims["causal_transfer_claimed"] is False,
        "top_failure_is_recurrent": bool(top_cluster and top_cluster.occurrences >= 3),
        "information_efficiency_positive": first.information_efficiency > 0.0,
    }
    certified = all(invariants.values())
    return {
        "status": (
            "CERTIFIED_LEARNING_INTELLIGENCE_FIXTURES_R0_3"
            if certified
            else "OAK_INVARIANT_FAILURE_R0_3"
        ),
        "system": "omega-code-dojo-t-infinity",
        "version": "R0.3",
        "receipt_count": len(receipts),
        "observation_count": first.observation_count,
        "best_learnings": [item.to_dict() for item in first.insights[:10]],
        "next_actions": [item.to_dict() for item in first_plan[:10]],
        "invariants": invariants,
        "report": first.to_dict(),
        "ledger": ledger.to_dict(),
        "ledger_entry": entry.to_dict(),
    }
