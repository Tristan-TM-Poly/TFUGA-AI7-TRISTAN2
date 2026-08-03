import math
import pytest

from omega_re_t.nonlinear_design_r06 import (
    ExperimentCandidate,
    ensemble_statistics,
    polynomial_predictor,
    score_experiments,
)


def test_ensemble_statistics_uniform():
    mean, variance = ensemble_statistics([0, 2])
    assert mean == pytest.approx(1)
    assert variance == pytest.approx(1)


def test_weighted_statistics():
    mean, variance = ensemble_statistics([0, 2], [3, 1])
    assert mean == pytest.approx(0.5)
    assert variance == pytest.approx(0.75)


def test_polynomial_predictor():
    predictor = polynomial_predictor((1, 2, 3))
    assert predictor((2,)) == 17
    with pytest.raises(ValueError):
        predictor((1, 2))


def test_design_selects_disagreement():
    candidates = (
        ExperimentCandidate("x1", (1,), 1, 0.1),
        ExperimentCandidate("x3", (3,), 1, 0.1),
    )
    report = score_experiments(candidates, (polynomial_predictor((0, 1)), polynomial_predictor((0, 1, 1))), budget=2, max_risk=0.2)
    assert report.selected_experiment_id == "x3"
    assert report.scores[0].predictive_variance > report.scores[1].predictive_variance


def test_unauthorized_and_irreversible_blocked():
    candidates = (
        ExperimentCandidate("unauth", (1,), 0, 0, authorized=False),
        ExperimentCandidate("irreversible", (2,), 0, 0, reversible=False),
    )
    report = score_experiments(candidates, (polynomial_predictor((0, 1)),), budget=1, max_risk=0.2)
    assert report.selected_experiment_id is None
    assert {item.reason for item in report.scores} == {"unauthorized", "irreversible"}
    assert all(item.utility == -math.inf for item in report.scores)


def test_budget_and_risk_gates():
    candidates = (
        ExperimentCandidate("expensive", (1,), 3, 0.1),
        ExperimentCandidate("risky", (1,), 1, 0.9),
    )
    report = score_experiments(candidates, (polynomial_predictor((0, 1)),), budget=2, max_risk=0.2)
    assert {item.reason for item in report.scores} == {"over_budget", "risk_exceeds_limit"}


def test_duplicate_candidate_rejected():
    candidate = ExperimentCandidate("same", (1,), 1, 0.1)
    with pytest.raises(ValueError):
        score_experiments((candidate, candidate), (polynomial_predictor((0, 1)),), budget=2, max_risk=0.2)


def test_invalid_novelty_rejected():
    with pytest.raises(ValueError):
        score_experiments((ExperimentCandidate("x", (1,), 1, 0.1),), (polynomial_predictor((0, 1)),), budget=2, max_risk=0.2, novelty={"x": -1})


def test_empty_predictors_rejected():
    with pytest.raises(ValueError):
        score_experiments((ExperimentCandidate("x", (1,), 1, 0.1),), (), budget=2, max_risk=0.2)
