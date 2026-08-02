from __future__ import annotations

"""Symmetry and anomaly compiler for Ω-PCT∞ R0.3 MAX.

This is a conservative structural compiler, not a replacement for a computer
algebra system or a full anomaly package. Unsupported representations are
reported as unresolved rather than guessed.
"""

from dataclasses import dataclass
from fractions import Fraction
import re
from typing import Iterable

from .types import Chirality, FieldKind, FieldSpec, FindingSeverity, TheorySpec, ValidationFinding


_GROUP_PATTERN = re.compile(r"^(?P<family>SU|SO|SP|U)(?P<n>[0-9]+)?(?:_?(?P<label>[A-Za-z][A-Za-z0-9]*))?$")


@dataclass(frozen=True, slots=True)
class LieGroup:
    id: str
    family: str
    n: int
    label: str | None = None

    @property
    def abelian(self) -> bool:
        return self.family == "U" and self.n == 1

    @property
    def rank(self) -> int:
        if self.family == "SU":
            return self.n - 1
        if self.family == "SO":
            return self.n // 2
        if self.family == "SP":
            return self.n
        if self.family == "U":
            return self.n
        raise ValueError(f"unsupported group family {self.family}")

    @property
    def algebra_dimension(self) -> int:
        if self.family == "SU":
            return self.n * self.n - 1
        if self.family == "SO":
            return self.n * (self.n - 1) // 2
        if self.family == "SP":
            return self.n * (2 * self.n + 1)
        if self.family == "U":
            return self.n * self.n
        raise ValueError(f"unsupported group family {self.family}")

    @property
    def canonical_name(self) -> str:
        suffix = f"_{self.label}" if self.label else ""
        return f"{self.family}{self.n}{suffix}"


@dataclass(frozen=True, slots=True)
class RepresentationInfo:
    group_id: str
    name: str
    dimension: int | None
    dynkin_index: Fraction | None
    cubic_anomaly_coefficient: Fraction | None
    real: bool | None


def parse_group(group_id: str) -> LieGroup:
    normalized = group_id.replace("(", "").replace(")", "").replace(" ", "")
    match = _GROUP_PATTERN.match(normalized)
    if match is None:
        raise ValueError(f"unsupported gauge group syntax: {group_id}")
    family = match.group("family")
    n_text = match.group("n")
    if family == "U" and n_text is None:
        n = 1
    elif n_text is None:
        raise ValueError(f"group rank parameter missing: {group_id}")
    else:
        n = int(n_text)
    if n < 1:
        raise ValueError(f"group parameter must be positive: {group_id}")
    if family == "SU" and n < 2:
        raise ValueError("SU(N) requires N >= 2")
    if family == "SO" and n < 2:
        raise ValueError("SO(N) requires N >= 2")
    return LieGroup(id=group_id, family=family, n=n, label=match.group("label"))


def representation_info(group: LieGroup, representation: str) -> RepresentationInfo:
    rep = representation.strip().lower()
    if rep in {"1", "singlet", "trivial"}:
        return RepresentationInfo(group.id, representation, 1, Fraction(0), Fraction(0), True)
    if group.abelian:
        return RepresentationInfo(group.id, representation, 1, None, None, True)
    if rep in {"fundamental", "fund", str(group.n)}:
        cubic = Fraction(0) if group.family in {"SO", "SP"} or group.n == 2 else Fraction(1)
        real = group.family in {"SO", "SP"} or (group.family == "SU" and group.n == 2)
        dynkin = Fraction(1, 2) if group.family == "SU" else Fraction(1)
        return RepresentationInfo(group.id, representation, group.n, dynkin, cubic, real)
    if rep in {"antifundamental", "anti-fundamental", f"{group.n}bar", f"bar{group.n}"}:
        cubic = Fraction(0) if group.family in {"SO", "SP"} or group.n == 2 else Fraction(-1)
        real = group.family in {"SO", "SP"} or (group.family == "SU" and group.n == 2)
        dynkin = Fraction(1, 2) if group.family == "SU" else Fraction(1)
        return RepresentationInfo(group.id, representation, group.n, dynkin, cubic, real)
    if rep in {"adjoint", "adj"}:
        return RepresentationInfo(
            group.id,
            representation,
            group.algebra_dimension,
            Fraction(group.n) if group.family == "SU" else None,
            Fraction(0),
            True,
        )
    return RepresentationInfo(group.id, representation, None, None, None, None)


def field_representation_dimension(field: FieldSpec, groups: dict[str, LieGroup]) -> int | None:
    result = 1
    for charge in field.gauge_charges:
        group = groups.get(charge.group_id)
        if group is None:
            return None
        info = representation_info(group, charge.representation)
        if info.dimension is None:
            return None
        result *= info.dimension
    return result


def signed_chiral_multiplicity(field: FieldSpec) -> int:
    if field.kind is not FieldKind.FERMION:
        return 0
    if field.chirality is Chirality.LEFT:
        return field.multiplicity
    if field.chirality is Chirality.RIGHT:
        return -field.multiplicity
    return 0


def u1_anomaly_sums(theory: TheorySpec, group_id: str) -> dict[str, Fraction]:
    cubic = Fraction(0)
    gravitational = Fraction(0)
    for field in theory.fields:
        sign_multiplicity = signed_chiral_multiplicity(field)
        if sign_multiplicity == 0:
            continue
        charge = field.charge_for(group_id)
        other_dimension = 1
        for gauge_charge in field.gauge_charges:
            if gauge_charge.group_id == group_id:
                continue
            try:
                group = parse_group(gauge_charge.group_id)
            except ValueError:
                other_dimension = 0
                break
            info = representation_info(group, gauge_charge.representation)
            if info.dimension is None:
                other_dimension = 0
                break
            other_dimension *= info.dimension
        weight = sign_multiplicity * other_dimension
        cubic += weight * charge**3
        gravitational += weight * charge
    return {"u1_cubic": cubic, "gravity_u1": gravitational}


def nonabelian_cubic_anomaly(theory: TheorySpec, group_id: str) -> Fraction | None:
    group = parse_group(group_id)
    total = Fraction(0)
    for field in theory.fields:
        sign_multiplicity = signed_chiral_multiplicity(field)
        if sign_multiplicity == 0:
            continue
        target_charge = next(
            (charge for charge in field.gauge_charges if charge.group_id == group_id),
            None,
        )
        if target_charge is None:
            continue
        info = representation_info(group, target_charge.representation)
        if info.cubic_anomaly_coefficient is None:
            return None
        spectator_dimension = 1
        for charge in field.gauge_charges:
            if charge.group_id == group_id:
                continue
            spectator_group = parse_group(charge.group_id)
            spectator_info = representation_info(spectator_group, charge.representation)
            if spectator_info.dimension is None:
                return None
            spectator_dimension *= spectator_info.dimension
        total += sign_multiplicity * spectator_dimension * info.cubic_anomaly_coefficient
    return total


def su2_witten_parity(theory: TheorySpec, group_id: str) -> int | None:
    group = parse_group(group_id)
    if group.family != "SU" or group.n != 2:
        return None
    doublets = 0
    for field in theory.fields:
        if field.kind is not FieldKind.FERMION or field.chirality is Chirality.VECTORLIKE:
            continue
        charge = next((item for item in field.gauge_charges if item.group_id == group_id), None)
        if charge is None:
            continue
        info = representation_info(group, charge.representation)
        if info.dimension is None:
            return None
        if info.dimension == 2:
            spectator = 1
            for other in field.gauge_charges:
                if other.group_id == group_id:
                    continue
                other_info = representation_info(parse_group(other.group_id), other.representation)
                if other_info.dimension is None:
                    return None
                spectator *= other_info.dimension
            doublets += field.multiplicity * spectator
    return doublets % 2


class SymmetryCompiler:
    def compile(self, theory: TheorySpec) -> tuple[ValidationFinding, ...]:
        findings: list[ValidationFinding] = []
        parsed_groups: dict[str, LieGroup] = {}
        for group_id in theory.gauge_groups:
            try:
                group = parse_group(group_id)
                parsed_groups[group_id] = group
                findings.append(
                    ValidationFinding(
                        gate="symmetry",
                        code="GROUP_PARSED",
                        severity=FindingSeverity.INFO,
                        message=(
                            f"{group_id}: rank={group.rank}, "
                            f"algebra_dimension={group.algebra_dimension}"
                        ),
                        object_id=group_id,
                    )
                )
            except ValueError as error:
                findings.append(
                    ValidationFinding(
                        gate="symmetry",
                        code="GROUP_UNSUPPORTED",
                        severity=FindingSeverity.ERROR,
                        message=str(error),
                        object_id=group_id,
                    )
                )
        for field in theory.fields:
            for charge in field.gauge_charges:
                if charge.group_id not in theory.gauge_groups:
                    findings.append(
                        ValidationFinding(
                            gate="symmetry",
                            code="UNDECLARED_GROUP",
                            severity=FindingSeverity.ERROR,
                            message=f"field {field.id} references undeclared {charge.group_id}",
                            object_id=field.id,
                        )
                    )
                    continue
                group = parsed_groups.get(charge.group_id)
                if group is None:
                    continue
                info = representation_info(group, charge.representation)
                if info.dimension is None:
                    findings.append(
                        ValidationFinding(
                            gate="symmetry",
                            code="REPRESENTATION_UNRESOLVED",
                            severity=FindingSeverity.WARNING,
                            message=(
                                f"representation {charge.representation} of {charge.group_id} "
                                "requires an external representation backend"
                            ),
                            object_id=field.id,
                        )
                    )
        findings.extend(self._anomaly_findings(theory, parsed_groups.values()))
        return tuple(findings)

    def _anomaly_findings(
        self,
        theory: TheorySpec,
        groups: Iterable[LieGroup],
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for group in groups:
            if group.abelian:
                sums = u1_anomaly_sums(theory, group.id)
                for anomaly_name, value in sums.items():
                    findings.append(
                        ValidationFinding(
                            gate="quantum_consistency",
                            code=("ANOMALY_CANCELLED" if value == 0 else "ANOMALY_NONZERO"),
                            severity=(FindingSeverity.INFO if value == 0 else FindingSeverity.ERROR),
                            message=f"{group.id} {anomaly_name} sum = {value}",
                            object_id=group.id,
                            evidence={"exact_fraction": str(value)},
                        )
                    )
            elif group.family == "SU":
                value = nonabelian_cubic_anomaly(theory, group.id)
                if value is None:
                    findings.append(
                        ValidationFinding(
                            gate="quantum_consistency",
                            code="ANOMALY_UNRESOLVED",
                            severity=FindingSeverity.WARNING,
                            message=f"{group.id} anomaly requires unsupported representation data",
                            object_id=group.id,
                        )
                    )
                else:
                    findings.append(
                        ValidationFinding(
                            gate="quantum_consistency",
                            code=("ANOMALY_CANCELLED" if value == 0 else "ANOMALY_NONZERO"),
                            severity=(FindingSeverity.INFO if value == 0 else FindingSeverity.ERROR),
                            message=f"{group.id} cubic anomaly sum = {value}",
                            object_id=group.id,
                            evidence={"exact_fraction": str(value)},
                        )
                    )
                parity = su2_witten_parity(theory, group.id)
                if parity is not None:
                    findings.append(
                        ValidationFinding(
                            gate="quantum_consistency",
                            code=("WITTEN_PARITY_EVEN" if parity == 0 else "WITTEN_PARITY_ODD"),
                            severity=(FindingSeverity.INFO if parity == 0 else FindingSeverity.ERROR),
                            message=f"{group.id} chiral doublet parity = {parity}",
                            object_id=group.id,
                        )
                    )
        return findings
