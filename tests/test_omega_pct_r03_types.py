from fractions import Fraction

from omega_pct_t.r03max.types import (
    EpistemicStatus,
    ScientificValue,
    SourceRef,
    Uncertainty,
    canonical_json,
    scientific_hash,
)


def test_established_value_requires_source():
    value = ScientificValue(1.0, "GeV", EpistemicStatus.ESTABLISHED)
    assert "requires provenance" in " ".join(value.validate())


def test_uncertainty_quadrature():
    uncertainty = Uncertainty(statistical=3.0, systematic=4.0)
    assert uncertainty.quadrature() == 5.0


def test_canonical_hash_is_stable():
    source = SourceRef("source", "v1")
    first = {"b": Fraction(1, 2), "a": source}
    second = {"a": source, "b": Fraction(1, 2)}
    assert canonical_json(first) == canonical_json(second)
    assert scientific_hash(first) == scientific_hash(second)
