from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from omega_code_dojo_t.r03.analyzer import LearningAnalyzer
from omega_code_dojo_t.r03.benchmark import fixture_receipts, run_r03_benchmark
from omega_code_dojo_t.r03.ingest import ReceiptError, normalize_receipts
from omega_code_dojo_t.r03.ledger import LearningLedger
from omega_code_dojo_t.r03.models import ActionKind, InsightKind, PlateauKind
from omega_code_dojo_t.r03.planner import LearningPlanner


def test_receipt_ingestion_and_metrics() -> None:
    observations, frontier = normalize_receipts(fixture_receipts())
    assert frontier == 3_221_225_472
    assert len(observations) == 20
    assert observations[0].information_efficiency > 0


def test_invalid_metric_is_rejected() -> None:
    receipt = deepcopy(fixture_receipts()[0])
    receipt["observations"][0]["mutation_score"] = 2.0
    with pytest.raises(ReceiptError):
        normalize_receipts((receipt,))


def test_analysis_is_deterministic() -> None:
    analyzer = LearningAnalyzer()
    first = analyzer.analyze(fixture_receipts())
    second = analyzer.analyze(deepcopy(fixture_receipts()))
    assert first.to_dict() == second.to_dict()
    assert len(first.report_sha256) == 64


def test_best_learning_classes_are_present() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts())
    kinds = {item.kind for item in report.insights}
    assert InsightKind.COUNTEREXAMPLE in kinds
    assert InsightKind.TEST_GAP in kinds
    assert InsightKind.TRANSFER in kinds
    assert InsightKind.STRATEGY in kinds


def test_recurrent_failures_are_prioritized() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts())
    assert report.failure_clusters
    assert report.failure_clusters[0].occurrences >= 3
    assert report.failure_clusters[0].repair_value > 0


def test_skill_uncertainty_is_explicit() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts())
    assert report.skills
    assert all(0 < item.mastery < 1 for item in report.skills)
    assert all(item.uncertainty > 0 for item in report.skills)


def test_plateau_is_distinguished() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts(), plateau_window=8)
    assert report.plateau.detected
    assert report.plateau.kind in {
        PlateauKind.NOVELTY,
        PlateauKind.INFORMATION,
        PlateauKind.EFFICIENCY,
        PlateauKind.MASTERY,
    }


def test_planner_prefers_repairs_and_has_stop_conditions() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts())
    actions = LearningPlanner().plan(report)
    kinds = {item.kind for item in actions}
    assert ActionKind.REPAIR_TEST in kinds or ActionKind.REPAIR_SKILL in kinds
    assert all(item.success_criterion for item in actions)
    assert all(item.stop_condition for item in actions)


def test_transfer_is_not_claimed_causal() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts())
    assert report.transfer_edges
    assert report.claims["causal_transfer_claimed"] is False


def test_ledger_chain_and_tamper_detection() -> None:
    report = LearningAnalyzer().analyze(fixture_receipts())
    ledger = LearningLedger()
    ledger.append(report)
    assert ledger.verify({report.report_id: report})
    tampered = replace(report, total_cost_units=report.total_cost_units + 1)
    assert not ledger.verify({report.report_id: tampered})


def test_empty_history_is_supported() -> None:
    report = LearningAnalyzer().analyze(())
    assert report.observation_count == 0
    assert report.coverage_ratio == 0
    assert report.insights == ()


def test_benchmark_certifies_only_internal_fixtures() -> None:
    payload = run_r03_benchmark()
    assert payload["status"] == "CERTIFIED_LEARNING_INTELLIGENCE_FIXTURES_R0_3"
    assert all(payload["invariants"].values())
    assert payload["report"]["claims"]["neural_training_claimed"] is False
