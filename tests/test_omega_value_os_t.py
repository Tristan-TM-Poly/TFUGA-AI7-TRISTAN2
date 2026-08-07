from __future__ import annotations

import json
import math

import pytest

from omega_value_os_t.cli import main
from omega_value_os_t.constitution import CONTEXT_PROFILES, constitution_payload
from omega_value_os_t.engine import evaluate_case, evaluate_portfolio, oak_report
from omega_value_os_t.fixtures import demo_cases
from omega_value_os_t.models import (
    AutonomyLevel,
    DecisionStatus,
    EvidenceLevel,
    ValueCase,
    stable_digest,
)
from omega_value_os_t.scoring import (
    claim_ceiling,
    debt_penalty,
    opportunity_costs,
    pareto_frontier,
    weighted_geometric_score,
)


def by_id():
    return {case.case_id: case for case in demo_cases()}


def test_demo_covers_review_abstain_and_blocked_states():
    reports = {report.case_id: report for report in (evaluate_case(case) for case in demo_cases())}
    assert reports["software.crystallized"].status is DecisionStatus.ELIGIBLE_FOR_HUMAN_REVIEW
    assert reports["research.fertile"].status is DecisionStatus.ABSTAIN
    assert reports["action.unsafe"].status is DecisionStatus.BLOCKED
    assert reports["claim.overreach"].status is DecisionStatus.BLOCKED


def test_hard_gate_is_non_compensatory():
    report = evaluate_case(by_id()["action.unsafe"])
    assert "safety" in report.failed_gates
    assert report.effective_value == 0.0
    assert report.hard_gate_passed is False


def test_claim_ceiling_blocks_overclaim():
    case = by_id()["claim.overreach"]
    report = evaluate_case(case)
    assert report.claim_ceiling < case.claim_strength
    assert report.claim_ceiling_respected is False
    assert "claim_ceiling" in report.failed_gates


def test_uncertainty_reduces_claim_ceiling():
    base = by_id()["software.crystallized"]
    low = ValueCase.from_dict({**base.to_dict(), "case_id": "low-u", "uncertainty": 0.0})
    high = ValueCase.from_dict({**base.to_dict(), "case_id": "high-u", "uncertainty": 1.0})
    assert claim_ceiling(high) < claim_ceiling(low)


def test_debt_penalty_is_monotone():
    base = by_id()["software.crystallized"]
    low = ValueCase.from_dict({**base.to_dict(), "case_id": "low-debt", "debts": {"risk": 0.0}})
    high = ValueCase.from_dict({**base.to_dict(), "case_id": "high-debt", "debts": {"risk": 2.0}})
    assert debt_penalty(high) < debt_penalty(low)
    assert math.isclose(debt_penalty(low), 1.0)


def test_weighted_geometric_score_penalizes_missing_profile_dimensions():
    base = by_id()["software.crystallized"]
    sparse = ValueCase.from_dict({
        **base.to_dict(),
        "case_id": "sparse",
        "dimensions": {"truth": 1.0},
    })
    full = weighted_geometric_score(base, CONTEXT_PROFILES["software"])
    partial = weighted_geometric_score(sparse, CONTEXT_PROFILES["software"])
    assert partial < full


def test_scores_are_never_serialized_as_probabilities():
    report = evaluate_case(by_id()["software.crystallized"]).payload()
    assert report["scores_are_probabilities"] is False
    assert report["automatic_merge_allowed"] is False
    assert report["automatic_publication_allowed"] is False
    assert report["external_action_performed"] is False


def test_a4_requires_human_approval():
    base = by_id()["software.crystallized"]
    case = ValueCase.from_dict({
        **base.to_dict(),
        "case_id": "a4-without-approval",
        "autonomy_level": int(AutonomyLevel.A4_BOUNDED_CONSEQUENCE),
        "human_approval": False,
    })
    report = evaluate_case(case)
    assert report.status is DecisionStatus.BLOCKED
    assert "high_consequence_human_approval" in report.failed_gates


def test_a3_requires_meaningful_reversibility():
    base = by_id()["software.crystallized"]
    case = ValueCase.from_dict({
        **base.to_dict(),
        "case_id": "a3-low-reversibility",
        "autonomy_level": int(AutonomyLevel.A3_REVERSIBLE_EXECUTION),
        "reversibility": 0.2,
    })
    report = evaluate_case(case)
    assert "insufficient_reversibility_for_autonomy" in report.failed_gates


def test_abstention_is_positive_governance_result():
    report = evaluate_case(by_id()["research.fertile"])
    assert report.status is DecisionStatus.ABSTAIN
    assert "Acquire" in report.next_action
    assert not report.failed_gates


def test_report_digest_is_deterministic_and_bound_to_input():
    case = by_id()["software.crystallized"]
    a = evaluate_case(case)
    b = evaluate_case(case)
    assert a.report_digest == b.report_digest
    changed = ValueCase.from_dict({**case.to_dict(), "case_id": "changed", "closure": 0.91})
    c = evaluate_case(changed)
    assert c.report_digest != a.report_digest
    assert c.input_digest != a.input_digest


def test_portfolio_is_deterministic_and_has_pareto_frontier():
    cases = demo_cases()
    a = evaluate_portfolio(cases)
    b = evaluate_portfolio(tuple(reversed(cases)))
    assert a["reports"] == b["reports"]
    assert a["pareto_frontier"] == b["pareto_frontier"]
    assert a["portfolio_digest"] == b["portfolio_digest"]
    assert a["pareto_frontier"]


def test_portfolio_duplicate_ids_fail_closed():
    case = by_id()["software.crystallized"]
    with pytest.raises(ValueError, match="unique"):
        evaluate_portfolio((case, case))


def test_pareto_dominance_keeps_non_dominated_cases():
    base = by_id()["software.crystallized"]
    low = ValueCase.from_dict({
        **base.to_dict(),
        "case_id": "low",
        "dimensions": {"truth": 0.2, "utility": 0.2},
    })
    high = ValueCase.from_dict({
        **base.to_dict(),
        "case_id": "high",
        "dimensions": {"truth": 0.8, "utility": 0.8},
    })
    assert pareto_frontier((low, high), ("truth", "utility")) == ("high",)


def test_opportunity_cost_is_gap_to_best_alternative():
    costs = opportunity_costs({"a": 0.9, "b": 0.5, "c": 0.2})
    assert costs["a"] == pytest.approx(0.4)
    assert costs["b"] == pytest.approx(0.4)
    assert costs["c"] == pytest.approx(0.7)


def test_invalid_score_fails_closed():
    payload = by_id()["software.crystallized"].to_dict()
    payload["dimensions"]["truth"] = 1.01
    with pytest.raises(ValueError, match="dimension.truth"):
        ValueCase.from_dict(payload)


def test_unknown_gate_fails_closed():
    payload = by_id()["software.crystallized"].to_dict()
    payload["hard_gates"]["profit"] = True
    with pytest.raises(ValueError, match="unknown hard gates"):
        ValueCase.from_dict(payload)


def test_missing_hard_gate_fails_closed():
    payload = by_id()["software.crystallized"].to_dict()
    del payload["hard_gates"]["consent"]
    with pytest.raises(ValueError, match="missing hard gates"):
        ValueCase.from_dict(payload)


def test_claim_requires_assumptions():
    payload = by_id()["software.crystallized"].to_dict()
    payload["assumptions"] = []
    with pytest.raises(ValueError, match="assumptions"):
        ValueCase.from_dict(payload)


def test_unknown_profile_fails_at_evaluation():
    base = by_id()["software.crystallized"]
    case = ValueCase.from_dict({**base.to_dict(), "case_id": "unknown-profile", "profile": "magic"})
    with pytest.raises(ValueError, match="unknown context profile"):
        evaluate_case(case)


def test_constitution_has_seven_kernels_and_review_only_authority():
    payload = constitution_payload()
    assert len(payload["kernels"]) == 7
    assert payload["authority"] == "review_only"
    assert payload["automatic_merge_allowed"] is False
    assert payload["external_action_performed"] is False


def test_oak_report_asserts_no_action_surface():
    payload = oak_report()
    assert payload["checks"]["hard_gates_non_compensatory"] is True
    assert payload["checks"]["external_action_surface"] is False
    assert payload["checks"]["automatic_merge_surface"] is False
    assert payload["checks"]["automatic_publication_surface"] is False


def test_cli_demo_is_deterministic(capsys):
    assert main(["demo"]) == 0
    first = capsys.readouterr().out
    assert main(["demo"]) == 0
    second = capsys.readouterr().out
    assert first == second
    payload = json.loads(first)
    assert payload["authority"] == "review_only"


def test_cli_evaluate_round_trip(tmp_path, capsys):
    case = by_id()["software.crystallized"]
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case.to_dict()), encoding="utf-8")
    assert main(["evaluate", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["case_id"] == case.case_id
    assert payload["input_digest"] == stable_digest(case.to_dict())


def test_cli_rejects_non_object_evaluate_input(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")
    assert main(["evaluate", str(path)]) == 2
    assert "JSON object" in capsys.readouterr().err


def test_high_consequence_profile_demands_stronger_evidence_floor():
    assert CONTEXT_PROFILES["high_consequence"].evidence_floor > CONTEXT_PROFILES["venture"].evidence_floor
