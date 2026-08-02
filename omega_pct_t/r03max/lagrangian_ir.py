from __future__ import annotations

"""Lagrangian intermediate representation and conservative compiler."""

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any, Mapping

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
    ScientificValue,
    SourceRef,
    TheorySpec,
    Uncertainty,
    canonical_json,
    scientific_hash,
)


def parse_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, Mapping) and "numerator" in value:
        return Fraction(int(value["numerator"]), int(value.get("denominator", 1)))
    return Fraction(str(value))


def _status(value: str | EpistemicStatus) -> EpistemicStatus:
    return value if isinstance(value, EpistemicStatus) else EpistemicStatus(value)


def _source(data: Mapping[str, Any] | None) -> SourceRef | None:
    if data is None:
        return None
    return SourceRef(
        source_id=str(data["source_id"]),
        version=str(data["version"]),
        locator=data.get("locator"),
        retrieved_at=data.get("retrieved_at"),
        sha256=data.get("sha256"),
        license=data.get("license"),
    )


def _uncertainty(data: Mapping[str, Any] | None) -> Uncertainty:
    if data is None:
        return Uncertainty()
    allowed = {
        "statistical",
        "systematic",
        "theoretical",
        "numerical",
        "model",
        "provenance",
        "unknown_unknown",
    }
    return Uncertainty(**{key: value for key, value in data.items() if key in allowed})


def _domain(data: Mapping[str, Any] | None) -> Domain:
    if data is None:
        return Domain()
    return Domain(
        energy_min_gev=data.get("energy_min_gev"),
        energy_max_gev=data.get("energy_max_gev"),
        temperature_min_k=data.get("temperature_min_k"),
        temperature_max_k=data.get("temperature_max_k"),
        medium=data.get("medium"),
        assumptions=tuple(data.get("assumptions", ())),
    )


def parse_scientific_value(data: Mapping[str, Any]) -> ScientificValue:
    return ScientificValue(
        value=data["value"],
        unit=data.get("unit"),
        status=_status(data.get("status", "unknown")),
        source=_source(data.get("source")),
        uncertainty=_uncertainty(data.get("uncertainty")),
        domain=_domain(data.get("domain")),
    )


def parse_field(data: Mapping[str, Any]) -> FieldSpec:
    charges = tuple(
        GaugeCharge.from_number(
            str(charge["group_id"]),
            str(charge.get("representation", "singlet")),
            charge.get("u1_charge"),
        )
        for charge in data.get("gauge_charges", ())
    )
    return FieldSpec(
        id=str(data["id"]),
        name=str(data.get("name", data["id"])),
        kind=FieldKind(data["kind"]),
        lorentz_representation=str(data["lorentz_representation"]),
        mass_dimension=parse_fraction(data["mass_dimension"]),
        ontology_level=OntologyLevel(data.get("ontology_level", "hypothetical")),
        status=_status(data.get("status", "hypothetical")),
        chirality=Chirality(data.get("chirality", "none")),
        gauge_charges=charges,
        multiplicity=int(data.get("multiplicity", 1)),
        real_field=bool(data.get("real_field", False)),
        antiparticle_id=data.get("antiparticle_id"),
        source=_source(data.get("source")),
        metadata=dict(data.get("metadata", {})),
    )


def parse_parameter(data: Mapping[str, Any]) -> ParameterSpec:
    return ParameterSpec(
        id=str(data["id"]),
        value=(parse_scientific_value(data["value"]) if isinstance(data.get("value"), Mapping) else None),
        lower=data.get("lower"),
        upper=data.get("upper"),
        prior=data.get("prior"),
        role=str(data.get("role", "free")),
    )


def parse_operator(data: Mapping[str, Any]) -> OperatorSpec:
    factors = tuple(
        OperatorFactor(
            field_id=str(item["field_id"]),
            multiplicity=int(item.get("multiplicity", 1)),
            conjugated=bool(item.get("conjugated", False)),
            derivatives=int(item.get("derivatives", 0)),
            tensor_role=item.get("tensor_role"),
        )
        for item in data.get("factors", ())
    )
    declared = data.get("declared_dimension")
    return OperatorSpec(
        id=str(data["id"]),
        coefficient=str(data["coefficient"]),
        factors=factors,
        declared_dimension=None if declared is None else parse_fraction(declared),
        hermitian=data.get("hermitian"),
        lorentz_scalar=data.get("lorentz_scalar"),
        status=_status(data.get("status", "hypothetical")),
        tags=tuple(data.get("tags", ())),
        source=_source(data.get("source")),
        metadata=dict(data.get("metadata", {})),
    )


def parse_theory(data: Mapping[str, Any]) -> TheorySpec:
    return TheorySpec(
        id=str(data["id"]),
        name=str(data.get("name", data["id"])),
        status=_status(data.get("status", "hypothetical")),
        baseline=data.get("baseline"),
        gauge_groups=tuple(str(item) for item in data.get("gauge_groups", ())),
        fields=tuple(parse_field(item) for item in data.get("fields", ())),
        parameters=tuple(parse_parameter(item) for item in data.get("parameters", ())),
        operators=tuple(parse_operator(item) for item in data.get("operators", ())),
        falsifiers=tuple(
            FalsifierSpec(
                id=str(item["id"]),
                statement=str(item["statement"]),
                observable=item.get("observable"),
                threshold=item.get("threshold"),
                experiment=item.get("experiment"),
            )
            for item in data.get("falsifiers", ())
        ),
        domain=_domain(data.get("domain")),
        source=_source(data.get("source")),
        metadata=dict(data.get("metadata", {})),
    )


def load_theory(path: str | Path) -> TheorySpec:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise TypeError("theory document root must be an object")
    return parse_theory(data)


def operator_mass_dimension(operator: OperatorSpec, theory: TheorySpec) -> Fraction:
    fields = theory.field_map()
    total = Fraction(0)
    for factor in operator.factors:
        field = fields.get(factor.field_id)
        if field is None:
            raise KeyError(f"operator {operator.id} references unknown field {factor.field_id}")
        total += factor.multiplicity * field.mass_dimension
        total += factor.derivatives
    return total


def operator_u1_charge(operator: OperatorSpec, theory: TheorySpec, group_id: str) -> Fraction:
    fields = theory.field_map()
    total = Fraction(0)
    for factor in operator.factors:
        field = fields[factor.field_id]
        sign = -1 if factor.conjugated else 1
        total += sign * factor.multiplicity * field.charge_for(group_id)
    return total


def operator_expression(operator: OperatorSpec) -> str:
    rendered: list[str] = []
    for factor in operator.factors:
        name = factor.field_id
        if factor.conjugated:
            name = f"conj({name})"
        if factor.derivatives:
            name = f"D^{factor.derivatives}({name})"
        if factor.multiplicity != 1:
            name = f"({name})^{factor.multiplicity}"
        rendered.append(name)
    return f"{operator.coefficient} * " + " * ".join(rendered)


@dataclass(frozen=True, slots=True)
class CompiledOperator:
    id: str
    expression: str
    mass_dimension: Fraction
    coupling_mass_dimension: Fraction
    u1_charges: Mapping[str, Fraction]
    gauge_invariant_u1: bool
    declared_dimension_matches: bool | None
    hermiticity_declared: bool | None
    lorentz_scalar_declared: bool | None


@dataclass(frozen=True, slots=True)
class CompiledTheory:
    theory_id: str
    fingerprint: str
    structural_errors: tuple[str, ...]
    operators: tuple[CompiledOperator, ...]
    equations_of_motion_ir: Mapping[str, tuple[str, ...]]
    metadata: Mapping[str, Any]

    @property
    def passed_structural_compilation(self) -> bool:
        return not self.structural_errors


class LagrangianCompiler:
    def compile(self, theory: TheorySpec) -> CompiledTheory:
        errors = list(theory.validate_structure())
        fields = theory.field_map()
        compiled: list[CompiledOperator] = []
        equations: dict[str, list[str]] = {field_id: [] for field_id in fields}
        abelian_groups = tuple(group for group in theory.gauge_groups if group.startswith("U1"))
        for operator in theory.operators:
            unknown = sorted(
                {factor.field_id for factor in operator.factors if factor.field_id not in fields}
            )
            if unknown:
                errors.append(
                    f"operator {operator.id} references unknown fields: {', '.join(unknown)}"
                )
                continue
            dimension = operator_mass_dimension(operator, theory)
            declared_matches = (
                None
                if operator.declared_dimension is None
                else operator.declared_dimension == dimension
            )
            if declared_matches is False:
                errors.append(
                    f"operator {operator.id} declared dimension {operator.declared_dimension} "
                    f"but computed {dimension}"
                )
            charges = {
                group: operator_u1_charge(operator, theory, group)
                for group in abelian_groups
            }
            for factor in operator.factors:
                equations[factor.field_id].append(
                    f"variation({operator.id}, {factor.field_id}, multiplicity={factor.multiplicity})"
                )
            compiled.append(
                CompiledOperator(
                    id=operator.id,
                    expression=operator_expression(operator),
                    mass_dimension=dimension,
                    coupling_mass_dimension=Fraction(4) - dimension,
                    u1_charges=charges,
                    gauge_invariant_u1=all(value == 0 for value in charges.values()),
                    declared_dimension_matches=declared_matches,
                    hermiticity_declared=operator.hermitian,
                    lorentz_scalar_declared=operator.lorentz_scalar,
                )
            )
        return CompiledTheory(
            theory_id=theory.id,
            fingerprint=scientific_hash(theory),
            structural_errors=tuple(errors),
            operators=tuple(compiled),
            equations_of_motion_ir={key: tuple(value) for key, value in equations.items()},
            metadata={
                "operator_count": len(compiled),
                "field_count": len(theory.fields),
                "parameter_count": len(theory.parameters),
                "canonical_theory_json": canonical_json(theory),
            },
        )
