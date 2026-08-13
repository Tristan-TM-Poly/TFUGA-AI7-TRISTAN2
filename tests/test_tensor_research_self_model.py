import pytest

from sage_tristan.tensor_discovery_bench import BenchmarkFamily, SystemKind
from sage_tristan.tensor_research_self_model import (
    CreditUnit,
    EpisodeLedger,
    MemoryClass,
    OutcomeClass,
    ResearchEpisode,
    build_self_model,
    compile_report,
    credit_receipt,
    deterministic_episode_ledger,
    predict,
    value_of_computation,
)


def test_r07_surface_becomes_32_append_only_episodes():
    ledger = deterministic_episode_ledger()
    assert ledger.append_only is True
    assert len(ledger.episodes) == 32
    assert len({item.episode_id for item in ledger.episodes}) == 32
    assert all(item.provenance_ids for item in ledger.episodes)
    assert all(item.external_scientific_validation is False for item in ledger.episodes)


def test_episode_ledger_rejects_duplicate_ids():
    ledger = deterministic_episode_ledger()
    with pytest.raises(ValueError):
        ledger.append(ledger.episodes[0])


def test_episode_validation_rejects_unbounded_proxy():
    with pytest.raises(ValueError):
        ResearchEpisode(
            episode_id="bad",
            problem_id="p",
            family=BenchmarkFamily.SYNTHETIC,
            system_kind=SystemKind.SINGLE_LLMT,
            selected_person_ids=("person_a",),
            operator_ids=("op",),
            representation_ids=("rep",),
            information_gain_proxy=1.2,
            declared_cost=0.1,
            declared_risk=0.1,
            calibration_proxy=0.5,
            hidden_target=True,
            contamination_controlled=True,
            outcome=OutcomeClass.POSITIVE,
            memory_class=MemoryClass.M_PLUS,
            provenance_ids=("fixture",),
        )


def test_three_memory_classes_are_preserved_as_distinct_states():
    model = build_self_model()
    counts = dict(model.memory_counts)
    assert set(counts) == {item.value for item in MemoryClass}
    assert sum(counts.values()) == model.episode_count
    assert counts[MemoryClass.M_PLUS.value] > 0
    assert counts[MemoryClass.M_MINUS.value] > 0
    assert counts[MemoryClass.M_QUESTION.value] > 0


def test_operator_credit_is_observational_not_causal():
    ledger = deterministic_episode_ledger()
    receipt = credit_receipt(ledger.episodes, CreditUnit.OPERATOR, "representation_switch")
    assert receipt.support_count > 0
    assert receipt.comparison_count > 0
    assert receipt.observational_only is True
    assert receipt.confounding_possible is True
    assert receipt.causal_credit_proven is False


def test_coalition_credit_is_observational_not_causal():
    ledger = deterministic_episode_ledger()
    receipt = credit_receipt(ledger.episodes, CreditUnit.COALITION, "person_a+person_b")
    assert receipt.support_count > 0
    assert receipt.causal_credit_proven is False
    assert receipt.confounding_possible is True


def test_prediction_requires_matching_history_and_never_claims_causality():
    ledger = deterministic_episode_ledger()
    receipt = predict(ledger.episodes, BenchmarkFamily.SYNTHETIC, SystemKind.META_LLMT)
    assert receipt.support_count == 1
    assert 0.0 <= receipt.predicted_information_gain_proxy <= 1.0
    assert receipt.predictive_association_only is True
    assert receipt.causal_effect_proven is False
    assert receipt.external_validity_proven is False


def test_value_of_computation_can_recommend_compute_or_reject_it():
    cheap = value_of_computation(
        "cheap",
        expected_information_gain_proxy=0.8,
        expected_cost=0.1,
        expected_risk=0.05,
        uncertainty=0.1,
    )
    expensive = value_of_computation(
        "expensive",
        expected_information_gain_proxy=0.3,
        expected_cost=0.6,
        expected_risk=0.2,
        uncertainty=0.4,
    )
    assert cheap.recommend_compute is True
    assert cheap.value_of_computation_proxy > 0
    assert expensive.recommend_compute is False
    assert expensive.value_of_computation_proxy < 0
    assert cheap.policy_proxy_only is True
    assert cheap.causal_effect_proven is False
    assert cheap.guaranteed_positive_return is False


def test_value_of_computation_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        value_of_computation(
            "bad",
            expected_information_gain_proxy=1.1,
            expected_cost=0.1,
            expected_risk=0.1,
            uncertainty=0.1,
        )


def test_compile_report_exposes_oak_boundaries():
    report = compile_report()
    assert report["release"] == "R0.8"
    assert report["episode_count"] == 32
    assert report["append_only_episode_ledger"] is True
    assert report["m_plus_is_truth"] is False
    assert report["m_minus_is_permanent_refutation"] is False
    assert report["m_question_preserved"] is True
    assert report["credit_is_causal_proof"] is False
    assert report["prediction_is_causal_effect"] is False
    assert report["value_of_computation_is_guaranteed_return"] is False
    assert report["benchmark_history_is_external_scientific_validation"] is False
    assert report["upstream_r07_required"] is True
    assert len(report["predictions"]) == 32
    assert any(item["recommend_compute"] is False for item in report["value_of_computation"])
    assert all(item["causal_credit_proven"] is False for item in report["operator_credits"])
    assert all(item["causal_credit_proven"] is False for item in report["coalition_credits"])
