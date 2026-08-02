from __future__ import annotations

"""Twelve-gate OAK validation for generated particle-field theories."""

from collections import defaultdict
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Iterable

from .lagrangian_ir import CompiledTheory, LagrangianCompiler
from .symmetry import SymmetryCompiler
from .types import FindingSeverity, TheorySpec, ValidationFinding, ValidationReport


GATES = (
    "syntax",
    "typing",
    "dimensions",
    "symmetry",
    "hermiticity_positivity",
    "conservation",
    "quantum_consistency",
    "known_limits",
    "numerics",
    "data",
    "falsification",
    "replication",
)


@dataclass(frozen=True, slots=True)
class OAKPolicy:
    require_source_for_established: bool = True
    require_falsifier: bool = True
    maximum_renormalizable_dimension: Fraction = Fraction(4)
    allow_unresolved_representations: bool = True
    fail_on_warning: bool = False


class OAKBench:
    def __init__(self, policy: OAKPolicy | None = None) -> None:
        self.policy = policy or OAKPolicy()
        self.lagrangian = LagrangianCompiler()
        self.symmetry = SymmetryCompiler()

    def evaluate(self, theory: TheorySpec) -> ValidationReport:
        findings: list[ValidationFinding] = [
            ValidationFinding(
                gate="syntax",
                code="THEORY_PARSED",
                severity=FindingSeverity.INFO,
                message="theory object is parsed and available to the compiler",
                object_id=theory.id,
            )
        ]
        compiled = self.lagrangian.compile(theory)
        findings.extend(self._structural_findings(compiled))
        findings.extend(self.symmetry.compile(theory))
        findings.extend(self._operator_findings(compiled))
        findings.extend(self._epistemic_findings(theory))
        findings.extend(self._falsification_findings(theory))
        findings.extend(self._replication_findings(theory, compiled))
        gate_results = self._gate_results(findings)
        return ValidationReport(
            theory_id=theory.id,
            findings=tuple(findings),
            gate_results=gate_results,
            metadata={
                "fingerprint": compiled.fingerprint,
                "policy": asdict(self.policy),
                "compiled_operator_count": len(compiled.operators),
                "oak_gate_count": len(GATES),
            },
        )

    def _structural_findings(self, compiled: CompiledTheory) -> list[ValidationFinding]:
        if not compiled.structural_errors:
            return [
                ValidationFinding(
                    gate="typing",
                    code="STRUCTURE_VALID",
                    severity=FindingSeverity.INFO,
                    message="typed theory structure validated",
                    object_id=compiled.theory_id,
                )
            ]
        return [
            ValidationFinding(
                gate="typing",
                code="STRUCTURE_ERROR",
                severity=FindingSeverity.ERROR,
                message=error,
                object_id=compiled.theory_id,
            )
            for error in compiled.structural_errors
        ]

    def _operator_findings(self, compiled: CompiledTheory) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for operator in compiled.operators:
            findings.append(
                ValidationFinding(
                    gate="dimensions",
                    code=(
                        "DIMENSION_VALID"
                        if operator.declared_dimension_matches is not False
                        else "DIMENSION_MISMATCH"
                    ),
                    severity=(
                        FindingSeverity.INFO
                        if operator.declared_dimension_matches is not False
                        else FindingSeverity.ERROR
                    ),
                    message=(
                        f"operator {operator.id}: dimension={operator.mass_dimension}, "
                        f"coupling_dimension={operator.coupling_mass_dimension}"
                    ),
                    object_id=operator.id,
                )
            )
            if operator.gauge_invariant_u1:
                findings.append(
                    ValidationFinding(
                        gate="symmetry",
                        code="U1_INVARIANT",
                        severity=FindingSeverity.INFO,
                        message=f"operator {operator.id} has zero declared U(1) charge",
                        object_id=operator.id,
                    )
                )
            else:
                findings.append(
                    ValidationFinding(
                        gate="symmetry",
                        code="U1_NONINVARIANT",
                        severity=FindingSeverity.ERROR,
                        message=f"operator {operator.id} violates a declared U(1)",
                        object_id=operator.id,
                        evidence={key: str(value) for key, value in operator.u1_charges.items()},
                    )
                )
            if operator.hermiticity_declared is True:
                findings.append(
                    ValidationFinding(
                        gate="hermiticity_positivity",
                        code="HERMITICITY_DECLARED",
                        severity=FindingSeverity.INFO,
                        message=f"operator {operator.id} declares hermiticity",
                        object_id=operator.id,
                    )
                )
            else:
                findings.append(
                    ValidationFinding(
                        gate="hermiticity_positivity",
                        code="HERMITICITY_UNRESOLVED",
                        severity=FindingSeverity.WARNING,
                        message=f"operator {operator.id} needs symbolic hermiticity proof",
                        object_id=operator.id,
                    )
                )
        return findings

    def _epistemic_findings(self, theory: TheorySpec) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        established_without_source = [
            field.id
            for field in theory.fields
            if field.status.value == "established" and field.source is None
        ]
        if established_without_source and self.policy.require_source_for_established:
            findings.append(
                ValidationFinding(
                    gate="data",
                    code="PROVENANCE_MISSING",
                    severity=FindingSeverity.ERROR,
                    message="established fields lack source provenance",
                    evidence={"field_ids": established_without_source},
                )
            )
        else:
            findings.append(
                ValidationFinding(
                    gate="data",
                    code="PROVENANCE_POLICY_SATISFIED",
                    severity=FindingSeverity.INFO,
                    message="declared provenance policy satisfied",
                )
            )
        if theory.baseline:
            findings.append(
                ValidationFinding(
                    gate="known_limits",
                    code="BASELINE_DECLARED",
                    severity=FindingSeverity.INFO,
                    message=f"baseline declared: {theory.baseline}",
                )
            )
        else:
            findings.append(
                ValidationFinding(
                    gate="known_limits",
                    code="BASELINE_MISSING",
                    severity=FindingSeverity.WARNING,
                    message="no known-theory baseline declared",
                )
            )
        findings.append(
            ValidationFinding(
                gate="numerics",
                code="NUMERICAL_BACKEND_NOT_RUN",
                severity=FindingSeverity.WARNING,
                message="structural OAKBench does not certify numerical convergence",
            )
        )
        findings.append(
            ValidationFinding(
                gate="conservation",
                code="CONSERVATION_REQUIRES_PROCESS",
                severity=FindingSeverity.WARNING,
                message="conservation testing requires compiled processes or equations of motion",
            )
        )
        return findings

    def _falsification_findings(self, theory: TheorySpec) -> list[ValidationFinding]:
        if theory.falsifiers:
            return [
                ValidationFinding(
                    gate="falsification",
                    code="FALSIFIERS_DECLARED",
                    severity=FindingSeverity.INFO,
                    message=f"{len(theory.falsifiers)} explicit falsifier(s) declared",
                )
            ]
        severity = FindingSeverity.ERROR if self.policy.require_falsifier else FindingSeverity.WARNING
        return [
            ValidationFinding(
                gate="falsification",
                code="FALSIFIER_MISSING",
                severity=severity,
                message="theory has no explicit rejection criterion",
            )
        ]

    def _replication_findings(
        self,
        theory: TheorySpec,
        compiled: CompiledTheory,
    ) -> list[ValidationFinding]:
        return [
            ValidationFinding(
                gate="replication",
                code="DETERMINISTIC_FINGERPRINT",
                severity=FindingSeverity.INFO,
                message="canonical theory fingerprint generated",
                evidence={"sha256": compiled.fingerprint},
            )
        ]

    def _gate_results(self, findings: Iterable[ValidationFinding]) -> dict[str, bool]:
        grouped: dict[str, list[ValidationFinding]] = defaultdict(list)
        for finding in findings:
            grouped[finding.gate].append(finding)
        result: dict[str, bool] = {}
        for gate in GATES:
            gate_findings = grouped.get(gate, [])
            if not gate_findings:
                result[gate] = False
                continue
            blocking = {FindingSeverity.ERROR, FindingSeverity.FATAL}
            if self.policy.fail_on_warning:
                blocking.add(FindingSeverity.WARNING)
            result[gate] = not any(item.severity in blocking for item in gate_findings)
        return result
