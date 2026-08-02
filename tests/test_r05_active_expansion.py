import math
import pytest

from omega_re_t.active_probabilistic_r05 import (
    FiniteHypothesis,
    entropy_bits,
    posterior_update,
    predictive_outcomes,
    run_active_campaign,
    score_experiment,
    select_experiment,
)
from omega_re_t.model_expansion_r05 import (
    ModelClass,
    effective_class_count,
    expand_model_classes,
    posterior_over_classes,
)


def hypotheses():
    return (
        FiniteHypothesis("a", {"x": {0: 0.9, 1: 0.1}, "y": {0: 0.5, 1: 0.5}}),
        FiniteHypothesis("b", {"x": {0: 0.1, 1: 0.9}, "y": {0: 0.5, 1: 0.5}}),
    )


def test_entropy_normalises_weights():
    assert entropy_bits({"a": 2, "b": 2}) == pytest.approx(1.0)


def test_posterior_update_concentrates():
    result = posterior_update(hypotheses(), {"a": 0.5, "b": 0.5}, "x", 0)
    assert result["a"] == pytest.approx(0.9)
    assert result["b"] == pytest.approx(0.1)


def test_predictive_distribution_is_normalised():
    result = predictive_outcomes(hypotheses(), {"a": 0.5, "b": 0.5}, "x")
    assert sum(result.values()) == pytest.approx(1.0)
    assert result[0] == pytest.approx(0.5)


def test_information_gain_prefers_discriminating_probe():
    informative = score_experiment(hypotheses(), {"a": 0.5, "b": 0.5}, "x")
    uninformative = score_experiment(hypotheses(), {"a": 0.5, "b": 0.5}, "y")
    assert informative.expected_information_gain_bits > uninformative.expected_information_gain_bits
    assert select_experiment(hypotheses(), {"a": 0.5, "b": 0.5}, ("y", "x")).experiment == "x"


def test_authorization_blocks_all_experiments():
    with pytest.raises(PermissionError):
        select_experiment(hypotheses(), {"a": 0.5, "b": 0.5}, ("x",), authorized=())


def test_campaign_respects_cost_budget():
    report = run_active_campaign(
        hypotheses(),
        {"a": 0.5, "b": 0.5},
        ("x", "y"),
        lambda experiment: 0,
        costs={"x": 2.0, "y": 1.0},
        cost_budget=1.5,
    )
    assert report.stopped_reason == "cost_budget_blocked"
    assert not report.observations


def test_campaign_reaches_low_entropy():
    report = run_active_campaign(
        hypotheses(),
        {"a": 0.5, "b": 0.5},
        ("x", "y"),
        lambda experiment: 0,
        entropy_target_bits=0.5,
    )
    assert report.final_posterior["a"] > 0.8
    assert len(report.observations) == 1


def test_model_class_posterior_penalises_complexity():
    classes = (
        ModelClass("simple", None, 1.0, -1.0, 0.1, "fixture"),
        ModelClass("complex", None, 10.0, -1.0, 0.1, "fixture"),
    )
    posterior = posterior_over_classes(classes, complexity_weight=0.2)
    assert posterior["simple"] > posterior["complex"]
    assert 1.0 <= effective_class_count(posterior) <= 2.0


def test_expansion_not_required_when_residual_low():
    root = ModelClass("root", None, 1.0, -1.0, 0.05, "fixture")
    decision = expand_model_classes((root,), lambda parent: (), residual_threshold=0.1)
    assert decision.expansion_required is False
    assert decision.trigger == "residual_within_threshold"


def test_expansion_filters_invalid_children():
    root = ModelClass("root", None, 1.0, -5.0, 1.0, "fixture")

    def generator(parent):
        yield ModelClass("good", "root", 2.0, -1.0, 0.1, "generated")
        yield ModelClass("bad-parent", "nope", 2.0, 0.0, 0.1, "generated")
        yield ModelClass("flat", "root", 1.0, 0.0, 0.1, "generated")

    decision = expand_model_classes((root,), generator, residual_threshold=0.2)
    assert decision.expansion_required is True
    assert any(item.class_id == "good" for item in decision.selected)
    assert ("bad-parent", "parent_mismatch") in decision.rejected
    assert ("flat", "complexity_not_expanded") in decision.rejected
