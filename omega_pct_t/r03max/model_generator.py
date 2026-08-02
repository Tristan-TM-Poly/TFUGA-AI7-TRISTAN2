from __future__ import annotations

"""Constraint-first theory candidate factories.

Generated models are research candidates, never discoveries. Factories attach
falsifiers and epistemic labels by construction.
"""

from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from itertools import product
from typing import Iterable, Iterator

from .types import (
    Chirality,
    Domain,
    EpistemicStatus,
    FieldKind,
    FieldSpec,
    FalsifierSpec,
    GaugeCharge,
    OntologyLevel,
    OperatorFactor,
    OperatorSpec,
    ParameterSpec,
    TheorySpec,
)


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def scalar_portal_candidate(
    *,
    scalar_id: str = "S",
    real_scalar: bool = True,
    z2_symmetric: bool = True,
) -> TheorySpec:
    suffix = "real" if real_scalar else "complex"
    symmetry = "z2" if z2_symmetric else "general"
    candidate_id = f"bsm.scalar-portal.{suffix}.{symmetry}"
    scalar = FieldSpec(
        id=scalar_id,
        name="dark scalar",
        kind=FieldKind.SCALAR,
        lorentz_representation="(0,0)",
        mass_dimension=Fraction(1),
        ontology_level=OntologyLevel.HYPOTHETICAL,
        status=EpistemicStatus.HYPOTHETICAL,
        real_field=real_scalar,
        gauge_charges=(GaugeCharge.from_number("U1Y", "singlet", 0),),
        metadata={"z2_symmetric": z2_symmetric},
    )
    factors = (
        OperatorFactor("H", conjugated=True),
        OperatorFactor("H"),
        OperatorFactor(scalar_id, multiplicity=2),
    )
    portal = OperatorSpec(
        id="operator.scalar_higgs_portal",
        coefficient="lambda_HS",
        factors=factors,
        declared_dimension=Fraction(4),
        hermitian=True,
        lorentz_scalar=True,
        status=EpistemicStatus.HYPOTHETICAL,
        tags=("portal", "bsm", "renormalizable"),
    )
    return TheorySpec(
        id=candidate_id,
        name="Scalar Higgs portal candidate",
        status=EpistemicStatus.HYPOTHETICAL,
        baseline="standard-model",
        gauge_groups=("SU3C", "SU2L", "U1Y"),
        fields=(
            FieldSpec(
                id="H",
                name="Higgs doublet",
                kind=FieldKind.SCALAR,
                lorentz_representation="(0,0)",
                mass_dimension=Fraction(1),
                ontology_level=OntologyLevel.FUNDAMENTAL,
                status=EpistemicStatus.EFFECTIVE,
                gauge_charges=(
                    GaugeCharge.from_number("SU2L", "fundamental"),
                    GaugeCharge.from_number("U1Y", "fundamental", Fraction(1, 2)),
                ),
            ),
            scalar,
        ),
        parameters=(
            ParameterSpec("lambda_HS", lower=-12.566, upper=12.566, prior="bounded_uniform"),
            ParameterSpec("m_S_gev", lower=0.0, prior="log_uniform"),
        ),
        operators=(portal,),
        falsifiers=(
            FalsifierSpec(
                id="falsifier.excluded-portal-space",
                statement="candidate point lies in experimentally excluded portal parameter space",
                observable="missing-energy, invisible-Higgs or direct-detection limits",
            ),
            FalsifierSpec(
                id="falsifier.vacuum-instability",
                statement="scalar potential is not bounded from below in the declared domain",
            ),
        ),
        domain=Domain(energy_min_gev=0.0, assumptions=("effective weak-scale description",)),
        metadata={"generator": "scalar_portal_candidate"},
    )


def dark_vector_candidate(
    *,
    dark_group: str = "U1D",
    kinetic_mixing_symbol: str = "epsilon",
) -> TheorySpec:
    vector = FieldSpec(
        id="X_mu",
        name="dark vector",
        kind=FieldKind.VECTOR,
        lorentz_representation="(1/2,1/2)",
        mass_dimension=Fraction(1),
        ontology_level=OntologyLevel.HYPOTHETICAL,
        status=EpistemicStatus.HYPOTHETICAL,
        gauge_charges=(GaugeCharge.from_number(dark_group, "adjoint", 0),),
        real_field=True,
    )
    hypercharge = FieldSpec(
        id="B_mu",
        name="hypercharge vector",
        kind=FieldKind.VECTOR,
        lorentz_representation="(1/2,1/2)",
        mass_dimension=Fraction(1),
        ontology_level=OntologyLevel.FUNDAMENTAL,
        status=EpistemicStatus.EFFECTIVE,
        gauge_charges=(GaugeCharge.from_number("U1Y", "adjoint", 0),),
        real_field=True,
    )
    kinetic_mixing = OperatorSpec(
        id="operator.kinetic_mixing",
        coefficient=kinetic_mixing_symbol,
        factors=(
            OperatorFactor("B_mu", derivatives=1, tensor_role="field_strength"),
            OperatorFactor("X_mu", derivatives=1, tensor_role="field_strength"),
        ),
        declared_dimension=Fraction(4),
        hermitian=True,
        lorentz_scalar=True,
        status=EpistemicStatus.HYPOTHETICAL,
        tags=("portal", "dark-vector", "renormalizable"),
    )
    return TheorySpec(
        id=f"bsm.dark-vector.{_slug(dark_group)}",
        name="Kinetically mixed dark vector candidate",
        status=EpistemicStatus.HYPOTHETICAL,
        baseline="standard-model",
        gauge_groups=("SU3C", "SU2L", "U1Y", dark_group),
        fields=(hypercharge, vector),
        parameters=(
            ParameterSpec(kinetic_mixing_symbol, lower=-1.0, upper=1.0, prior="log_abs"),
            ParameterSpec("m_X_gev", lower=0.0, prior="log_uniform"),
        ),
        operators=(kinetic_mixing,),
        falsifiers=(
            FalsifierSpec(
                id="falsifier.dark-vector-exclusion",
                statement="the parameter point is excluded by applicable accelerator, astrophysical or precision constraints",
            ),
            FalsifierSpec(
                id="falsifier.gauge-inconsistency",
                statement="the UV completion has uncancelled gauge anomalies or violates unitarity",
            ),
        ),
        domain=Domain(assumptions=("effective kinetic-mixing model",)),
        metadata={"generator": "dark_vector_candidate"},
    )


def vectorlike_fermion_candidate(
    *,
    color_representations: Iterable[str] = ("singlet", "fundamental"),
    weak_representations: Iterable[str] = ("singlet", "fundamental"),
    hypercharges: Iterable[Fraction] = (Fraction(0), Fraction(1), Fraction(-1)),
) -> Iterator[TheorySpec]:
    for color_rep, weak_rep, hypercharge in product(
        color_representations,
        weak_representations,
        hypercharges,
    ):
        token = f"{color_rep}|{weak_rep}|{hypercharge}"
        digest = sha256(token.encode("utf-8")).hexdigest()[:12]
        field = FieldSpec(
            id=f"Psi_{digest}",
            name="vectorlike fermion candidate",
            kind=FieldKind.FERMION,
            lorentz_representation="Dirac",
            mass_dimension=Fraction(3, 2),
            ontology_level=OntologyLevel.HYPOTHETICAL,
            status=EpistemicStatus.HYPOTHETICAL,
            chirality=Chirality.VECTORLIKE,
            gauge_charges=(
                GaugeCharge.from_number("SU3C", color_rep),
                GaugeCharge.from_number("SU2L", weak_rep),
                GaugeCharge.from_number("U1Y", "fundamental", hypercharge),
            ),
        )
        mass = OperatorSpec(
            id=f"operator.vectorlike-mass.{digest}",
            coefficient=f"M_{digest}",
            factors=(
                OperatorFactor(field.id, conjugated=True),
                OperatorFactor(field.id),
            ),
            declared_dimension=Fraction(3),
            hermitian=True,
            lorentz_scalar=True,
            status=EpistemicStatus.HYPOTHETICAL,
            tags=("vectorlike", "mass"),
        )
        yield TheorySpec(
            id=f"bsm.vectorlike-fermion.{digest}",
            name=f"Vectorlike fermion {color_rep}/{weak_rep}/Y={hypercharge}",
            status=EpistemicStatus.HYPOTHETICAL,
            baseline="standard-model",
            gauge_groups=("SU3C", "SU2L", "U1Y"),
            fields=(field,),
            parameters=(ParameterSpec(f"M_{digest}", lower=0.0, prior="log_uniform"),),
            operators=(mass,),
            falsifiers=(
                FalsifierSpec(
                    id=f"falsifier.mass-limit.{digest}",
                    statement="mass and coupling point is excluded by applicable searches",
                ),
            ),
            metadata={"generator": "vectorlike_fermion_candidate", "token": token},
        )


def attach_operator(theory: TheorySpec, operator: OperatorSpec) -> TheorySpec:
    return replace(theory, operators=theory.operators + (operator,))
