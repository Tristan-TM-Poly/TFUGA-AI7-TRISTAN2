"""Advanced exact, graph and residual tests for Ω-SUITE-FORM-T∞ R∞."""
from __future__ import annotations

from fractions import Fraction
import json

import pytest

from omega_sequence_forms_t.rinf import (
    DiscoveryLimits,
    EdgeKind,
    NodeKind,
    RepresentationEdge,
    RepresentationHypergraph,
    RepresentationNode,
    ResidualCandidate,
    discover_rational_prony,
    discover_rinf,
    greedy_residual_decompose,
    hankel_rank_profile,
)
from omega_sequence_forms_t.rinf.graph import sequence_graph_fixture
from omega_sequence_forms_t.rinf.hankel import (
    characteristic_from_recurrence,
    determinant,
    divide_by_linear,
    hankel_matrix,
    matrix_rank,
    polynomial_value,
    rational_roots,
)
from omega_sequence_forms_t.rinf.residual import affine_factory, constant_factory, periodic_factory


def test_hankel_matrix_and_exact_rank() -> None:
    terms = [Fraction(1), Fraction(2), Fraction(4), Fraction(8), Fraction(16)]
    matrix = hankel_matrix(terms, 2, 3)
    assert matrix == (
        (Fraction(1), Fraction(2), Fraction(4)),
        (Fraction(2), Fraction(4), Fraction(8)),
    )
    assert matrix_rank(matrix) == 1


def test_hankel_determinant() -> None:
    matrix = (
        (Fraction(1), Fraction(2), Fraction(3)),
        (Fraction(0), Fraction(1), Fraction(4)),
        (Fraction(5), Fraction(6), Fraction(0)),
    )
    assert determinant(matrix) == 1
    assert determinant(((Fraction(1), Fraction(2)), (Fraction(2), Fraction(4)))) == 0


def test_hankel_rank_profile_detects_two_exponentials() -> None:
    terms = tuple(Fraction(2) ** n + 3 * Fraction(5) ** n for n in range(20))
    profile = hankel_rank_profile(terms, max_size=8)
    assert profile.ranks[:2] == (1, 2)
    assert all(rank == 2 for rank in profile.ranks[1:])
    assert profile.stable_rank == 2


def test_characteristic_polynomial_convention() -> None:
    # a_n = 7 a_{n-1} - 10 a_{n-2}; roots 2 and 5.
    characteristic = characteristic_from_recurrence((Fraction(7), Fraction(-10)))
    assert characteristic == (Fraction(10), Fraction(-7), Fraction(1))
    assert polynomial_value(characteristic, Fraction(2)) == 0
    assert polynomial_value(characteristic, Fraction(5)) == 0


def test_rational_root_factorization() -> None:
    polynomial = (Fraction(10), Fraction(-7), Fraction(1))
    roots = rational_roots(polynomial)
    assert roots is not None
    assert set(roots) == {Fraction(2), Fraction(5)}
    quotient = divide_by_linear(polynomial, Fraction(2))
    assert quotient == (Fraction(-5), Fraction(1))


def test_rational_roots_refuse_repeated_and_irrational_factors() -> None:
    assert rational_roots((Fraction(1), Fraction(-2), Fraction(1))) is None
    assert rational_roots((Fraction(-2), Fraction(0), Fraction(1))) is None


def test_rational_prony_recovers_two_terms_and_holdout() -> None:
    terms = tuple(Fraction(2) ** n + 3 * Fraction(5) ** n for n in range(32))
    candidates = discover_rational_prony(terms, max_order=6, holdout=8)
    assert candidates
    candidate = candidates[0]
    assert candidate.rank == 2
    assert candidate.predicts_holdout
    assert {term.root for term in candidate.terms} == {Fraction(2), Fraction(5)}
    assert candidate.evaluate(40) == Fraction(2) ** 40 + 3 * Fraction(5) ** 40


def test_rational_prony_refuses_fibonacci_irrational_roots() -> None:
    terms = [Fraction(0), Fraction(1)]
    for _ in range(30):
        terms.append(terms[-1] + terms[-2])
    assert discover_rational_prony(terms, max_order=4, holdout=6) == ()


def test_representation_graph_fixture_and_reachability() -> None:
    graph = sequence_graph_fixture()
    assert graph.validate() == []
    reached = graph.reachable(("seq",))
    assert {"seq", "rec", "gf", "proof"} <= reached
    exact = graph.reachable(("rec",), exact_only=True)
    assert "gf" in exact
    assert len(graph.digest()) == 64


def test_representation_graph_rejects_unknown_nodes() -> None:
    graph = RepresentationHypergraph("bad")
    graph.add_node(RepresentationNode("a", NodeKind.SEQUENCE, "a", {}))
    with pytest.raises(KeyError):
        graph.add_edge(
            RepresentationEdge(
                "edge",
                EdgeKind.REPRESENTS,
                ("a",),
                ("missing",),
                "x",
                False,
                False,
                (),
                (),
            )
        )


def test_representation_graph_rejects_approximate_proof_edge() -> None:
    graph = RepresentationHypergraph("proof")
    graph.add_node(RepresentationNode("claim", NodeKind.FORM, "claim", {}))
    graph.add_node(RepresentationNode("proof", NodeKind.EVIDENCE, "proof", {}))
    graph.add_edge(
        RepresentationEdge(
            "edge",
            EdgeKind.PROVES,
            ("proof",),
            ("claim",),
            "formal",
            False,
            False,
            (),
            (),
        )
    )
    assert graph.validate() == ["edge: proof edge cannot be approximate"]


def test_graphml_projection_is_deterministic() -> None:
    graph = sequence_graph_fixture()
    first = graph.graphml()
    second = graph.graphml()
    assert first == second
    assert "<graphml" in first
    assert "hyperedge" in first
    assert "fixture.fibonacci" in first


def test_residual_constant_decomposition_roundtrip() -> None:
    values = [Fraction(7)] * 20
    decomposition = greedy_residual_decompose(values, (constant_factory,), maximum_layers=4)
    assert decomposition.stop_reason == "zero_residual"
    assert len(decomposition.layers) == 1
    assert decomposition.exact_roundtrip()
    assert all(value == 0 for value in decomposition.residual)


def test_residual_affine_decomposition_roundtrip() -> None:
    values = [Fraction(3 + 5 * n) for n in range(20)]
    decomposition = greedy_residual_decompose(values, (affine_factory, constant_factory), maximum_layers=4)
    assert decomposition.stop_reason == "zero_residual"
    assert decomposition.layers[0].family_id == "affine"
    assert decomposition.exact_roundtrip()


def test_residual_periodic_decomposition() -> None:
    pattern = (Fraction(1), Fraction(-2), Fraction(4))
    values = tuple(pattern[n % 3] for n in range(30))
    decomposition = greedy_residual_decompose(values, (periodic_factory(8),), maximum_layers=3)
    assert decomposition.stop_reason == "zero_residual"
    assert decomposition.layers[0].family_id == "periodic"
    assert decomposition.exact_roundtrip()


def test_residual_layers_can_combine_affine_and_periodic() -> None:
    pattern = (Fraction(2), Fraction(-1))
    values = tuple(Fraction(10 + 3 * n) + pattern[n % 2] for n in range(40))

    def known_affine(_values: tuple[Fraction, ...]):
        return (
            ResidualCandidate(
                candidate_id="known-affine",
                family_id="affine",
                expression="10+3n",
                evaluator=lambda n: Fraction(10 + 3 * n),
                complexity=4,
            ),
        )

    decomposition = greedy_residual_decompose(
        values,
        (known_affine, periodic_factory(4)),
        maximum_layers=4,
    )
    assert decomposition.stop_reason == "zero_residual"
    assert [layer.family_id for layer in decomposition.layers] == ["affine", "periodic"]
    assert decomposition.exact_roundtrip()


def test_residual_threshold_prevents_unhelpful_layer() -> None:
    values = [Fraction(1), Fraction(-1)] * 10
    decomposition = greedy_residual_decompose(
        values,
        (constant_factory,),
        maximum_layers=4,
        minimum_gain=1000,
    )
    assert decomposition.layers == []
    assert decomposition.stop_reason == "marginal_gain_threshold"


def test_residual_report_digest_is_stable() -> None:
    values = [Fraction(4)] * 12
    first = greedy_residual_decompose(values, (constant_factory,), maximum_layers=2)
    second = greedy_residual_decompose(values, (constant_factory,), maximum_layers=2)
    assert first.to_dict() == second.to_dict()
    assert first.digest() == second.digest()


def test_orchestrator_builds_multifamily_graph() -> None:
    terms = tuple(Fraction(2) ** n + 3 * Fraction(5) ** n for n in range(32))
    report = discover_rinf(
        terms,
        limits=DiscoveryLimits(max_period=8, max_degree=4, max_order=6, max_candidates_per_family=4, holdout=8),
    )
    payload = report.to_dict()
    assert payload["candidate_count"] >= 1
    assert payload["families"]["rational_prony"]
    assert payload["diagnostics"]["hankel_rank_profile"]["stable_rank"] == 2
    assert payload["representation_graph"]["validation_errors"] == []
    assert payload["global_identity_proved"] is False
    assert payload["formal_proof_completed"] is False
    assert len(payload["report_digest"]) == 64


def test_orchestrator_is_deterministic() -> None:
    terms = tuple(Fraction(2) ** n + Fraction(3) ** n for n in range(28))
    limits = DiscoveryLimits(max_period=6, max_degree=3, max_order=5, max_candidates_per_family=3, holdout=6)
    first = discover_rinf(terms, limits=limits).to_dict()
    second = discover_rinf(terms, limits=limits).to_dict()
    assert first == second


def test_orchestrator_no_candidate_keeps_oak_warning() -> None:
    terms = tuple(Fraction((n * n + 7) % 11) for n in range(17))
    report = discover_rinf(
        terms,
        limits=DiscoveryLimits(max_period=3, max_degree=1, max_order=2, max_candidates_per_family=1, holdout=4),
    )
    payload = report.to_dict()
    assert payload["global_identity_proved"] is False
    assert any("Finite-prefix agreement" in warning for warning in payload["warnings"])
