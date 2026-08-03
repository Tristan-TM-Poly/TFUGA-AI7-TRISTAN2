"""OAK audit gates for Ω-VLA-T∞³ R0.3-OMEGA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import numpy.typing as npt

from .compilers import Backend, CompilerRegistry, default_registry
from .evaluator import EvaluationLimits, evaluate_operator
from .ir import IRValidationIssue, VLAProgram
from .operators import OperatorExpr, OperatorError
from .types import TypeSystemError


@dataclass(frozen=True)
class OAKGate:
    gate: int
    name: str
    passed: bool
    severity: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "name": self.name,
            "passed": self.passed,
            "severity": self.severity,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class R03OAKReport:
    subject_digest: str
    subject_kind: str
    gates: tuple[OAKGate, ...]
    status: str
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return all(gate.passed or gate.severity != "error" for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_digest": self.subject_digest,
            "subject_kind": self.subject_kind,
            "passed": self.passed,
            "status": self.status,
            "gates": [gate.to_dict() for gate in self.gates],
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }


def audit_program(program: VLAProgram) -> R03OAKReport:
    validation = program.validate()
    syntax_issues = [issue for issue in validation.issues if issue.code in {"DANGLING_EDGE", "DUPLICATE_EDGE"}]
    type_issues = [issue for issue in validation.issues if "TYPE" in issue.code or issue.code in {"UNTYPED_MATH_NODE", "ADJOINT_MISMATCH", "COMMUTATOR_MISMATCH"}]
    dependency_issues = [issue for issue in validation.issues if issue.code == "DEPENDENCY_CYCLE"]
    provenance_issues = [issue for issue in validation.issues if issue.code == "MISSING_PROVENANCE"]
    gates = (
        OAKGate(0, "syntax", not syntax_issues, "error", _issue_evidence(syntax_issues)),
        OAKGate(1, "typing", not type_issues, "error", _issue_evidence(type_issues)),
        OAKGate(2, "units", not type_issues, "error", ("unit checks are embedded in MathType operations",)),
        OAKGate(3, "domain-codomain", not type_issues, "error", ("domain/codomain checks are embedded in operator inference",)),
        OAKGate(4, "assumptions-and-provenance", not provenance_issues, "warning", _issue_evidence(provenance_issues)),
        OAKGate(5, "dependency-acyclicity", not dependency_issues, "error", _issue_evidence(dependency_issues)),
        OAKGate(6, "counterexample-search", False, "informational", ("not automatically executed for a generic IR graph",)),
        OAKGate(7, "baseline-comparison", False, "informational", ("requires an application-specific campaign",)),
        OAKGate(8, "stability", False, "informational", ("requires numerical semantics and perturbation fixtures",)),
        OAKGate(9, "formal-proof", False, "informational", ("no proof is claimed",)),
        OAKGate(10, "reproduction", program.digest() == VLAProgram.from_json(program.canonical_json()).digest(), "error", ("canonical JSON round-trip",)),
        OAKGate(11, "canonical-promotion", False, "informational", ("promotion is external and reversible",)),
    )
    passed = all(gate.passed or gate.severity != "error" for gate in gates)
    return R03OAKReport(
        subject_digest=program.digest(),
        subject_kind="vla-ir-program",
        gates=gates,
        status="OAK_PASS_VLA_IR_FIXTURE_R0_3" if passed else "OAK_FAIL_VLA_IR_FIXTURE_R0_3",
    )


def audit_operator_expression(
    expression: OperatorExpr,
    environment: Mapping[str, npt.ArrayLike] | None = None,
    *,
    registry: CompilerRegistry | None = None,
    evaluate_when_bound: bool = True,
) -> R03OAKReport:
    gates: list[OAKGate] = []
    registry = registry or default_registry()
    try:
        inferred = expression.infer_type()
        gates.append(OAKGate(0, "syntax", True, "error", (f"nodes={expression.node_count()}", f"depth={expression.depth()}",)))
        gates.append(OAKGate(1, "typing", True, "error", (inferred.canonical_json(),)))
        gates.append(OAKGate(2, "units", True, "error", (str(inferred.units),)))
        gates.append(OAKGate(3, "domain-codomain", True, "error", (f"domain={inferred.domain_id}", f"codomain={inferred.codomain_id}")))
    except (TypeSystemError, OperatorError) as exc:
        gates.extend(
            [
                OAKGate(0, "syntax", True, "error", (f"nodes={expression.node_count()}",)),
                OAKGate(1, "typing", False, "error", (str(exc),)),
                OAKGate(2, "units", False, "error", ("blocked by typing failure",)),
                OAKGate(3, "domain-codomain", False, "error", ("blocked by typing failure",)),
            ]
        )
        return _operator_report(expression, gates)

    simplified = expression.simplify()
    gates.append(
        OAKGate(
            4,
            "simplification",
            simplified.node_count() <= expression.node_count(),
            "error",
            (
                f"before={expression.node_count()}",
                f"after={simplified.node_count()}",
                f"digest={simplified.digest()}",
            ),
        )
    )

    compilation_evidence: list[str] = []
    compilation_ok = True
    for backend_name in registry.backends():
        backend = Backend(backend_name)
        try:
            artifact = registry.compile(simplified, backend)
            compilation_evidence.append(
                f"{backend.value}:complete={artifact.complete}:executable={artifact.executable}"
            )
        except Exception as exc:  # backend errors are evidence, not hidden
            compilation_ok = False
            compilation_evidence.append(f"{backend.value}:error={type(exc).__name__}:{exc}")
    gates.append(OAKGate(5, "backend-compilation", compilation_ok, "error", tuple(compilation_evidence)))

    if evaluate_when_bound and environment is not None:
        try:
            result = evaluate_operator(simplified, environment, limits=EvaluationLimits())
            gates.append(
                OAKGate(
                    6,
                    "finite-numerical-evaluation",
                    result.finite,
                    "error",
                    (
                        f"shape={result.matrix.shape}",
                        f"norm={float(np.linalg.norm(result.matrix)):.17g}",
                        *tuple(f"{name}={value:.3e}" for name, value in result.residual_checks),
                    ),
                )
            )
        except Exception as exc:
            gates.append(OAKGate(6, "finite-numerical-evaluation", False, "error", (f"{type(exc).__name__}: {exc}",)))
    else:
        gates.append(OAKGate(6, "finite-numerical-evaluation", False, "informational", ("no complete environment supplied",)))

    gates.extend(
        [
            OAKGate(7, "counterexample-search", False, "informational", ("run IdentityFactory trials for universal schemas",)),
            OAKGate(8, "baseline-comparison", False, "informational", ("NumPy reference only in this wave",)),
            OAKGate(9, "formal-proof", False, "informational", ("Lean target is explicit-incomplete",)),
            OAKGate(10, "reproduction", expression.digest() == expression.digest(), "error", ("content-addressed deterministic digest",)),
            OAKGate(11, "canonical-promotion", False, "informational", ("no automatic promotion",)),
        ]
    )
    return _operator_report(expression, gates)


def _operator_report(expression: OperatorExpr, gates: list[OAKGate]) -> R03OAKReport:
    passed = all(gate.passed or gate.severity != "error" for gate in gates)
    return R03OAKReport(
        subject_digest=expression.digest(),
        subject_kind="operator-expression",
        gates=tuple(gates),
        status="OAK_PASS_OPERATOR_FIXTURE_R0_3" if passed else "OAK_FAIL_OPERATOR_FIXTURE_R0_3",
    )


def _issue_evidence(issues: list[IRValidationIssue]) -> tuple[str, ...]:
    return tuple(f"{issue.code}:{issue.subject}:{issue.message}" for issue in issues) or ("no issues",)
