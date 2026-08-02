from fractions import Fraction

from omega_pct_t.r03max.symmetry import parse_group, u1_anomaly_sums
from omega_pct_t.r03max.types import (
    Chirality,
    EpistemicStatus,
    FieldKind,
    FieldSpec,
    GaugeCharge,
    OntologyLevel,
    TheorySpec,
)


def fermion(identifier: str, charge: int, chirality: Chirality) -> FieldSpec:
    return FieldSpec(
        id=identifier,
        name=identifier,
        kind=FieldKind.FERMION,
        lorentz_representation="Weyl",
        mass_dimension=Fraction(3, 2),
        ontology_level=OntologyLevel.HYPOTHETICAL,
        status=EpistemicStatus.HYPOTHETICAL,
        chirality=chirality,
        gauge_charges=(GaugeCharge.from_number("U1X", "fundamental", charge),),
    )


def test_group_dimensions():
    assert parse_group("SU3C").algebra_dimension == 8
    assert parse_group("SU2L").rank == 1
    assert parse_group("U1Y").abelian


def test_vectorlike_u1_anomaly_cancels():
    theory = TheorySpec(
        id="vectorlike",
        name="vectorlike",
        status=EpistemicStatus.HYPOTHETICAL,
        baseline=None,
        gauge_groups=("U1X",),
        fields=(fermion("left", 1, Chirality.LEFT), fermion("right", 1, Chirality.RIGHT)),
        parameters=(),
        operators=(),
        falsifiers=(),
    )
    sums = u1_anomaly_sums(theory, "U1X")
    assert sums["u1_cubic"] == 0
    assert sums["gravity_u1"] == 0


def test_chiral_u1_anomaly_is_detected():
    theory = TheorySpec(
        id="chiral",
        name="chiral",
        status=EpistemicStatus.HYPOTHETICAL,
        baseline=None,
        gauge_groups=("U1X",),
        fields=(fermion("left", 1, Chirality.LEFT),),
        parameters=(),
        operators=(),
        falsifiers=(),
    )
    assert u1_anomaly_sums(theory, "U1X")["u1_cubic"] == 1
