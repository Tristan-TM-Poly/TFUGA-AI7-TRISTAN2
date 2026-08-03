"""OAKBench tests for Ω-SUITE-FORM-T∞ R∞."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

import pytest

from omega_sequence_forms_t.rinf import (
    CampaignBudget,
    CandidatePredictor,
    CellAddress,
    CellSpace,
    EvidenceArtifact,
    EvidenceLevel,
    FailureObservation,
    FormCandidateRInf,
    NegativeMemoryRegistry,
    TraversalSlice,
    assert_catalog_invariants,
    build_antipattern_catalog,
    build_family_catalog,
    build_transformation_catalog,
    catalog_payload,
    discover_hypergeometric,
    discover_p_recursive,
    discover_quasi_polynomials,
    discover_rational_indices,
    evaluate_promotion,
    iter_addresses,
    materialize_catalog,
    materialize_cells,
    rank_discriminating_indices,
    run_benchmark,
    run_campaign,
    sample_addresses,
)
from omega_sequence_forms_t.rinf.active import geometric_index_frontier
from omega_sequence_forms_t.rinf.address import FeistelPermutation, cell_space_receipt, shard_for
from omega_sequence_forms_t.rinf.benchmark import synthetic_fixture_stream
from omega_sequence_forms_t.rinf.campaign import campaign_summary, deterministic_estimator
from omega_sequence_forms_t.rinf.hypergeometric import central_binomial_fixture, factorial_fixture
from omega_sequence_forms_t.rinf.materialize import materialization_receipt
from omega_sequence_forms_t.rinf.mminus import minimize_counterexample
from omega_sequence_forms_t.rinf.oak import EvidenceGraph, validate_candidate_consistency
from omega_sequence_forms_t.rinf.p_recursive import fit_p_recursive, verify_operator
from omega_sequence_forms_t.rinf.quasipolynomial import fit_quasi_polynomial, quasi_polynomial_fixture
from omega_sequence_forms_t.rinf.rational_index import fit_rational_index, rational_fixture


def test_catalog_cardinalities_and_deterministic_digest() -> None:
    assert_catalog_invariants()
    families = build_family_catalog()
    transformations = build_transformation_catalog()
    antipatterns = build_antipattern_catalog()
    assert len(families) == 256
    assert len(transformations) == 512
    assert len(antipatterns) == 1024
    first = catalog_payload()
    second = catalog_payload()
    assert first == second
    assert first["counts"] == {
        "families": 256,
        "transformations": 512,
        "antipatterns": 1024,
    }
    assert first["permanent_total_cap"] is None


def test_catalog_ids_and_indices_are_unique() -> None:
    families = build_family_catalog()
    transformations = build_transformation_catalog()
    antipatterns = build_antipattern_catalog()
    assert [item.index for item in families] == list(range(256))
    assert [item.index for item in transformations] == list(range(512))
    assert [item.index for item in antipatterns] == list(range(1024))
    all_ids = (
        [item.family_id for item in families]
        + [item.transformation_id for item in transformations]
        + [item.antipattern_id for item in antipatterns]
    )
    assert len(all_ids) == len(set(all_ids))


def test_cvcd_oak_and_mminus_transformations_remain_canonical() -> None:
    slugs = {item.transformation_id for item in build_transformation_catalog()}
    assert any("cvcd_extract" in item for item in slugs)
    assert any("oak_gate" in item for item in slugs)
    assert any("mminus_update" in item for item in slugs)
    assert not any("normalize_scale" in item for item in slugs)
    assert not any("unit_check" in item for item in slugs)
    assert not any("noether_residue" in item for item in slugs)


def test_default_cell_space_has_34_billion_addresses() -> None:
    space = CellSpace()
    assert space.shape == (256, 512, 128, 64, 32)
    assert space.logical_cells == 34_359_738_368
    receipt = cell_space_receipt(space)
    assert receipt["matches_default"] is True
    assert receipt["permanent_total_cap"] is None


@pytest.mark.parametrize(
    "index",
    [0, 1, 31, 32, 4096, 1_000_000, 34_359_738_367],
)
def test_cell_flatten_roundtrip(index: int) -> None:
    space = CellSpace()
    address = space.unflatten(index)
    assert CellAddress.parse(address.render()) == address
    assert space.flatten(address) == index


def test_cell_address_rejects_invalid_text() -> None:
    with pytest.raises(ValueError):
        CellAddress.parse("family.1")
    with pytest.raises(ValueError):
        CellAddress(-1, 0, 0, 0, 0)


def test_feistel_permutation_is_deterministic_and_collision_free_prefix() -> None:
    permutation = FeistelPermutation(10_003, seed=42)
    first = [permutation.permute(index) for index in range(1000)]
    second = [permutation.permute(index) for index in range(1000)]
    assert first == second
    assert len(first) == len(set(first))
    assert all(0 <= value < 10_003 for value in first)


def test_address_sampling_does_not_allocate_logical_space() -> None:
    sample = sample_addresses(100, seed=123)
    assert len(sample) == 100
    assert len(set(sample)) == 100
    assert sample == sample_addresses(100, seed=123)
    assert sample != sample_addresses(100, seed=124)


def test_traversal_slice_and_sharding() -> None:
    space = CellSpace(4, 5, 3, 2, 2)
    addresses = tuple(iter_addresses(space=space, seed=9, traversal=TraversalSlice(3, 33, 2)))
    assert len(addresses) == 15
    assert len(set(addresses)) == len(addresses)
    shards = [shard_for(address, 7, space=space) for address in addresses]
    assert all(0 <= shard < 7 for shard in shards)


def test_quasi_polynomial_exact_detection_and_holdout() -> None:
    terms = quasi_polynomial_fixture(period=3, degree=3, count=60)
    candidates = discover_quasi_polynomials(terms, max_period=8, max_degree=5)
    assert candidates
    candidate = candidates[0]
    assert candidate.period == 3
    assert candidate.maximum_degree == 3
    assert candidate.exact_fit
    assert candidate.predicts_holdout
    assert all(candidate.evaluate(index) == value for index, value in enumerate(terms))


def test_quasi_polynomial_rejects_wrong_period_fit() -> None:
    terms = quasi_polynomial_fixture(period=5, degree=2, count=70)
    assert fit_quasi_polynomial(terms, period=2, max_degree=3) is None


def test_quasi_polynomial_adversarial_tail_is_demoted() -> None:
    terms = list(quasi_polynomial_fixture(period=4, degree=2, count=64))
    terms[-1] += 17
    candidates = discover_quasi_polynomials(terms, max_period=8, max_degree=4)
    assert not candidates or not candidates[0].predicts_holdout


def test_rational_index_exact_detection() -> None:
    terms = rational_fixture((2, 3, 1), (1, 2), 64)
    candidates = discover_rational_indices(
        terms,
        max_numerator_degree=4,
        max_denominator_degree=4,
    )
    assert candidates
    candidate = candidates[0]
    assert candidate.predicts_holdout
    assert candidate.numerator_degree <= 2
    assert candidate.denominator_degree <= 1
    assert all(candidate.evaluate(index) == value for index, value in enumerate(terms))


def test_rational_index_requires_overdetermination() -> None:
    terms = rational_fixture((1, 2), (1, 1), 4)
    assert fit_rational_index(terms, numerator_degree=2, denominator_degree=1, holdout=0) is None


def test_rational_index_rejects_singular_normalization_domain() -> None:
    values = [Fraction(1, n + 1) for n in range(20)]
    candidate = fit_rational_index(values, numerator_degree=0, denominator_degree=1, holdout=4)
    assert candidate is not None
    assert candidate.denominator[0] == 1


def test_hypergeometric_factorial_detection() -> None:
    terms = factorial_fixture(36)
    candidates = discover_hypergeometric(terms, max_numerator_degree=3, max_denominator_degree=3)
    assert candidates
    candidate = candidates[0]
    assert candidate.predicts_holdout
    assert candidate.evaluate(35) == terms[35]
    assert candidate.evaluate(36) == terms[35] * 36


def test_hypergeometric_central_binomial_detection() -> None:
    terms = central_binomial_fixture(40)
    candidates = discover_hypergeometric(terms, max_numerator_degree=4, max_denominator_degree=4)
    assert candidates
    assert candidates[0].predicts_holdout
    assert all(candidates[0].evaluate(index) == value for index, value in enumerate(terms))


def test_hypergeometric_refuses_zero_crossings() -> None:
    assert discover_hypergeometric([1, 2, 0, 4, 8, 16]) == ()


def test_hypergeometric_adversarial_tail_is_demoted() -> None:
    terms = list(central_binomial_fixture(40))
    terms[-1] += 1
    candidates = discover_hypergeometric(terms, max_numerator_degree=4, max_denominator_degree=4)
    assert not candidates or not candidates[0].predicts_holdout


def test_p_recursive_factorial_operator() -> None:
    terms = factorial_fixture(48)
    candidates = discover_p_recursive(terms, max_order=3, max_degree=3)
    assert candidates
    candidate = candidates[0]
    assert candidate.predicts_holdout
    matches, equations = verify_operator(candidate.operator, terms)
    assert matches == equations
    assert candidate.operator.order == 1
    assert candidate.operator.degree <= 1


def test_p_recursive_recurrence_with_constant_coefficients() -> None:
    terms = [Fraction(0), Fraction(1)]
    for _ in range(40):
        terms.append(terms[-1] + terms[-2])
    candidates = discover_p_recursive(terms, max_order=4, max_degree=2)
    assert candidates
    assert candidates[0].operator.order <= 2
    matches, equations = verify_operator(candidates[0].operator, terms)
    assert matches == equations


def test_p_recursive_rejects_underdetermined_shell() -> None:
    terms = factorial_fixture(8)
    assert fit_p_recursive(terms, order=4, degree=2, holdout_equations=0) == ()


def test_p_recursive_adversarial_mutation_fails_remote_equation() -> None:
    terms = list(factorial_fixture(48))
    training = tuple(terms[:36])
    candidates = discover_p_recursive(training, max_order=3, max_degree=3, holdout_equations=4)
    assert candidates
    terms[-1] += 1
    matches, equations = verify_operator(candidates[0].operator, terms)
    assert matches < equations


def test_active_index_selects_maximum_disagreement() -> None:
    predictors = (
        CandidatePredictor("linear", lambda n: n),
        CandidatePredictor("square", lambda n: n * n),
        CandidatePredictor("constant", lambda n: 0),
    )
    ranked = rank_discriminating_indices(predictors, range(1, 10))
    assert ranked
    assert ranked[0].distinct_predictions == 3
    assert ranked[0].numerical_spread is not None
    assert ranked[0].index >= 2


def test_active_index_records_domain_failures() -> None:
    def failing(n: int) -> int:
        raise ZeroDivisionError("fixture")

    ranked = rank_discriminating_indices(
        (CandidatePredictor("ok", lambda n: n), CandidatePredictor("bad", failing)),
        [7],
    )
    assert ranked[0].prediction_count == 1
    assert ranked[0].failures[0][0] == "bad"


def test_geometric_frontier_is_remote_and_deterministic() -> None:
    first = geometric_index_frontier(100, layers=8, dense_radius=8)
    second = geometric_index_frontier(100, layers=8, dense_radius=8)
    assert first == second
    assert min(first) >= 100
    assert max(first) >= 100 * 2**7


def _candidate(level: EvidenceLevel = EvidenceLevel.OBSERVED_FIT) -> FormCandidateRInf:
    return FormCandidateRInf(
        candidate_id="candidate.fixture",
        family_id="family.fixture",
        expression="a_n=n^2",
        parameters={},
        assumptions=("n in N",),
        evidence_level=level,
        observed_terms=20,
        observed_matches=20,
        held_out_terms=5,
        held_out_matches=5,
        adversarial_checks=4,
        adversarial_passes=4,
    )


def test_oak_promotion_to_holdout() -> None:
    decision = evaluate_promotion(_candidate(), EvidenceLevel.HELD_OUT_PREDICTION)
    assert decision.accepted
    assert decision.granted_level == EvidenceLevel.HELD_OUT_PREDICTION


def test_oak_refuses_global_proof_without_proof_artifact() -> None:
    decision = evaluate_promotion(
        _candidate(EvidenceLevel.ADVERSARIAL_VALIDATION),
        EvidenceLevel.MATHEMATICAL_PROOF,
        completed_checks={"complete_argument", "all_quantifiers_scoped", "assumptions_explicit"},
        independent_provenance={"independent-a"},
    )
    assert not decision.accepted
    assert decision.granted_level <= EvidenceLevel.SYMBOLIC_IDENTITY
    assert any("global proof" in reason for reason in decision.reasons)


def test_oak_consistency_errors() -> None:
    candidate = FormCandidateRInf(
        candidate_id="bad",
        family_id="family",
        expression="x",
        parameters={},
        assumptions=(),
        evidence_level=EvidenceLevel.HELD_OUT_PREDICTION,
        observed_terms=4,
        observed_matches=3,
    )
    errors = validate_candidate_consistency(candidate)
    assert "OAK-1 requires complete observed fit" in errors
    assert "OAK-2 requires complete held-out prediction" in errors


def test_evidence_graph_rejects_cycles_and_has_stable_digest() -> None:
    graph = EvidenceGraph()
    first = EvidenceArtifact.from_payload(
        artifact_id="a",
        kind="fixture",
        statement="a",
        provenance="test",
        payload={"x": 1},
        reproducible=True,
    )
    second = EvidenceArtifact.from_payload(
        artifact_id="b",
        kind="fixture",
        statement="b",
        provenance="test",
        payload={"x": 2},
        reproducible=True,
    )
    graph.add(first)
    graph.add(second, depends_on=("a",))
    assert graph.closure(("b",)) == {"a", "b"}
    assert graph.digest() == graph.digest()


def test_negative_memory_catalog_and_recording() -> None:
    registry = NegativeMemoryRegistry()
    assert len(registry.catalog) == 1024
    antipattern = registry.catalog[0]
    observation = FailureObservation(
        observation_id="obs-1",
        antipattern_id=antipattern.antipattern_id,
        candidate_id="candidate-1",
        address=CellAddress(0, 0, 0, 0, 0),
        minimal_input=("1", "4", "9", "17"),
        expected="16",
        observed="17",
        reproduction="pytest fixture",
        provenance="unit-test",
        severity=5,
    )
    digest = registry.record(observation)
    assert len(digest) == 64
    assert registry.receipt()["active_observations"] == 1
    registry.resolve("obs-1", "held-out validation added")
    assert registry.receipt()["resolved_observations"] == 1


def test_negative_memory_matching_and_promotion_ceiling() -> None:
    registry = NegativeMemoryRegistry()
    matches = registry.match(
        risk_tags={"vacuous", "interpolation"},
        context="exact_integer",
        detector_codes={"degree"},
    )
    assert matches
    ceiling = registry.promotion_ceiling(matches[:10])
    assert ceiling <= EvidenceLevel.FORMAL_PROOF


def test_counterexample_delta_debugging() -> None:
    values = ("a", "b", "FAIL", "c", "d")
    minimized = minimize_counterexample(values, lambda items: "FAIL" in items)
    assert minimized == ("FAIL",)


def test_campaign_is_deterministic_under_cell_budget() -> None:
    budget = CampaignBudget(
        compute_units=10_000,
        materialized_cell_cap=128,
        minimum_marginal_value=0.0,
        minimum_value_cost_ratio=0.0,
    )
    first = run_campaign(campaign_id="fixture", seed=77, budget=budget, initial_frontier=256)
    second = run_campaign(campaign_id="fixture", seed=77, budget=budget, initial_frontier=256)
    assert first.to_dict() == second.to_dict()
    assert first.executed_cells == 128
    assert first.stop_reason == "campaign_materialized_cell_cap"
    assert first.permanent_total_cap is None


def test_campaign_threshold_stops_without_permanent_cap() -> None:
    budget = CampaignBudget(minimum_value_cost_ratio=1_000_000)
    receipt = run_campaign(campaign_id="threshold", seed=1, budget=budget, initial_frontier=64)
    assert receipt.executed_cells == 0
    assert receipt.stop_reason == "value_cost_threshold"
    assert receipt.budget.has_permanent_cell_cap is False


def test_campaign_summary_compresses_results() -> None:
    budget = CampaignBudget(materialized_cell_cap=16, compute_units=1000)
    receipt = run_campaign(campaign_id="summary", seed=2, budget=budget, initial_frontier=64)
    summary = campaign_summary(receipt)
    assert summary["results"]["count"] == receipt.executed_cells
    assert len(summary["receipt_digest"]) == 64


def test_catalog_materialization_is_deterministic(tmp_path: Path) -> None:
    first = materialize_catalog(tmp_path / "a.jsonl", budget=CampaignBudget(storage_megabytes=32))
    second = materialize_catalog(tmp_path / "b.jsonl", budget=CampaignBudget(storage_megabytes=32))
    assert first.record_count == 1792
    assert first.sha256 == second.sha256
    assert (tmp_path / "a.jsonl").read_bytes() == (tmp_path / "b.jsonl").read_bytes()


def test_cell_materialization_respects_campaign_budget(tmp_path: Path) -> None:
    budget = CampaignBudget(materialized_cell_cap=1000, storage_megabytes=32)
    stats = materialize_cells(tmp_path / "cells.jsonl", seed=99, budget=budget)
    assert stats.record_count == 1000
    assert stats.stop_reason == "campaign_materialized_cell_cap"
    lines = (tmp_path / "cells.jsonl").read_text().splitlines()
    assert len(lines) == 1000
    payload = json.loads(lines[0])
    assert payload["status"] == "unexecuted_research_cell"
    assert payload["global_identity_proved"] is False


def test_materialization_receipt_preserves_no_permanent_cap(tmp_path: Path) -> None:
    budget = CampaignBudget(materialized_cell_cap=32, storage_megabytes=8)
    catalog_stats = materialize_catalog(tmp_path / "catalog.jsonl", budget=CampaignBudget(storage_megabytes=8))
    cell_stats = materialize_cells(tmp_path / "cells.jsonl", seed=5, budget=budget)
    receipt = materialization_receipt(
        catalog_stats=catalog_stats,
        cell_stats=cell_stats,
        budget=budget,
        seed=5,
    )
    assert receipt["materialized_cells"] == 32
    assert receipt["permanent_total_cap"] is None
    assert len(receipt["receipt_digest"]) == 64


def test_synthetic_fixture_stream_is_unbounded_and_deterministic() -> None:
    first_stream = synthetic_fixture_stream(seed=11)
    second_stream = synthetic_fixture_stream(seed=11)
    first = [next(first_stream) for _ in range(10_000)]
    second = [next(second_stream) for _ in range(10_000)]
    assert first == second
    assert len({item["fixture_id"] for item in first}) == 10_000
    assert {item["family"] for item in first} == {
        "quasi_polynomial",
        "rational_index",
        "hypergeometric",
        "p_recursive",
    }


def test_full_rinf_benchmark_receipt() -> None:
    payload = run_benchmark(campaign_cells=64, seed=314159)
    assert payload["passed"] is True
    assert payload["catalog"]["counts"]["families"] == 256
    assert payload["cell_space"]["logical_cells"] == 34_359_738_368
    assert payload["campaign"]["executed_cells"] == 64
    assert payload["global_identity_proved"] is False
    assert payload["formal_proof_completed"] is False
    assert len(payload["benchmark_digest"]) == 64


def test_benchmark_is_deterministic() -> None:
    first = run_benchmark(campaign_cells=32, seed=1234)
    second = run_benchmark(campaign_cells=32, seed=1234)
    assert first == second
