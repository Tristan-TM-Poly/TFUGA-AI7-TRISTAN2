import operator

import pytest

from omega_pure_math_t import (
    FactorizationWitness,
    Invariant,
    NegativeMathEntry,
    NegativeMathRegistry,
    StructuralDNA,
    THEOREM_CANDIDATES,
    all_parenthesizations,
    bracket_spectrum,
    compose_witnesses,
    cvcd_matrix,
    generate_research_protocol,
    minimal_sufficient_subsets,
    oak_audit_claims,
    subadditivity_certificate,
    zero_triple_defect_on,
)


def test_catalan_parenthesization_counts():
    assert len(all_parenthesizations(1)) == 1
    assert len(all_parenthesizations(3)) == 2
    assert len(all_parenthesizations(4)) == 5
    assert len(all_parenthesizations(5)) == 14


def test_t2_associative_operation_has_zero_bracket_diameter():
    spectrum = bracket_spectrum([2, 3, 5, 7], operator.add)
    assert spectrum.parenthesization_count == 5
    assert spectrum.value_count == 1
    assert spectrum.diameter == 0.0
    assert zero_triple_defect_on(range(-2, 3), operator.add)


def test_nonassociative_operation_exposes_positive_bracket_diameter():
    spectrum = bracket_spectrum([10, 3, 2], operator.sub)
    assert spectrum.parenthesization_count == 2
    assert spectrum.value_count == 2
    assert spectrum.diameter > 0
    assert not zero_triple_defect_on([1, 2, 3], operator.sub)


def test_t1_constructive_factorization_subadditivity():
    left = FactorizationWitness("X", ("A", "B"))
    right = FactorizationWitness("Y", ("C",))
    composite = compose_witnesses(left, right, composite_name="X⊗Y")
    assert composite.bricks == ("A", "B", "C")
    assert subadditivity_certificate(left, right, composite)
    assert composite.length == left.length + right.length


def test_t3_invariant_obstruction():
    dimension = Invariant("dimension", len)
    assert dimension.obstructs_isomorphism([1, 2], [1, 2, 3])
    assert not dimension.obstructs_isomorphism([1, 2], ["a", "b"])


def test_cvcd_matrix_is_symmetric_for_symmetric_metric():
    matrix = cvcd_matrix(
        representations=[1.0, 2.5, 4.0],
        property_fn=lambda x: x,
        metric=lambda a, b: abs(a - b),
    )
    assert matrix[0][0] == 0
    assert matrix[0][2] == matrix[2][0] == 3.0


def test_minimal_hypothesis_search_finds_multiple_minima():
    minima = minimal_sufficient_subsets(
        ["A", "B", "C"],
        lambda subset: ("A" in subset and "B" in subset) or "C" in subset,
    )
    assert frozenset({"C"}) in minima
    assert frozenset({"A", "B"}) in minima
    assert len(minima) == 2


def test_negative_math_registry_preserves_failure_reason():
    registry = NegativeMathRegistry()
    registry.add(
        NegativeMathEntry(
            hypothesis="all operations are associative",
            counterexample="subtraction",
            failure_reason="(a-b)-c != a-(b-c)",
            repaired_hypothesis="restrict to an associative operation",
        )
    )
    assert registry.search("associative")
    assert not registry.search("topology")


def test_structural_dna_is_canonical_and_detects_differences():
    left = StructuralDNA.from_mapping(
        {"invariants": ["rank", "dimension"], "symmetries": ["C2"]}
    )
    reordered = StructuralDNA.from_mapping(
        {"symmetries": ["C2"], "invariants": ["dimension", "rank"]}
    )
    right = StructuralDNA.from_mapping(
        {"invariants": ["rank"], "symmetries": ["C2"]}
    )
    assert left == reordered
    assert left.digest() == reordered.digest()
    assert left.collision(reordered)
    assert left.jaccard_distance(right) > 0
    assert left.differing_fields(right) == ("invariants",)


def test_protocol_has_exactly_twelve_distinct_research_questions():
    protocol = generate_research_protocol("BracketSpectrum")
    assert len(protocol) == 12
    assert len({item.kind for item in protocol}) == 12


def test_oak_registry_keeps_hard_targets_as_conjectures():
    report = oak_audit_claims(THEOREM_CANDIDATES)
    assert report.accepted
    status = {claim.identifier: claim.status.value for claim in THEOREM_CANDIDATES}
    assert status["T1"] == "theorem"
    assert status["T2"] == "theorem"
    assert status["T3"] == "theorem"
    assert status["T8"] == "conjecture"


def test_empty_parenthesization_rejected():
    with pytest.raises(ValueError):
        all_parenthesizations(0)
