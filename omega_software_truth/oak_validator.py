"""OAK validator for executable software hypotheses."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .contracts import ContractCheck, all_checks_passed
from .software_state import ExampleCase, SoftwareState


@dataclass(frozen=True)
class CaseResult:
    name: str
    passed: bool
    input_checks: list[ContractCheck] = field(default_factory=list)
    output_checks: list[ContractCheck] = field(default_factory=list)
    exception_checks: list[ContractCheck] = field(default_factory=list)
    output: Any | None = None
    exception: str | None = None
    residue: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation of a case result."""

        return {
            "name": self.name,
            "passed": self.passed,
            "input_checks": [_check_to_dict(check) for check in self.input_checks],
            "output_checks": [_check_to_dict(check) for check in self.output_checks],
            "exception_checks": [_check_to_dict(check) for check in self.exception_checks],
            "output_repr": repr(self.output),
            "exception": self.exception,
            "residue": self.residue,
        }


@dataclass(frozen=True)
class OAKReport:
    state_name: str
    verdict: str
    passed: bool
    total_cases: int
    passed_cases: int
    failed_cases: int
    residues: list[str]
    case_results: list[CaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe OAK report dictionary."""

        return {
            "state_name": self.state_name,
            "verdict": self.verdict,
            "passed": self.passed,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "residues": list(self.residues),
            "case_results": [case.to_dict() for case in self.case_results],
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the report as deterministic UTF-8 JSON text."""

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            f"# OAK REPORT — {self.state_name}",
            "",
            f"**Verdict:** {self.verdict}",
            f"**Passed:** {self.passed}",
            f"**Cases:** {self.passed_cases}/{self.total_cases}",
            "",
            "## Residues",
        ]
        lines.extend(f"- {residue}" for residue in self.residues or ["None"])
        lines.extend(["", "## Case results"])
        for case in self.case_results:
            status = "PASS" if case.passed else "FAIL"
            lines.append(f"- `{case.name}`: {status}" + (f" — {case.residue}" if case.residue else ""))
        return "\n".join(lines) + "\n"


class OAKValidator:
    """Validate a SoftwareState as a falsifiable behavioral hypothesis."""

    def validate(self, state: SoftwareState) -> OAKReport:
        results = [self._run_case(state, case) for case in state.examples]
        passed_cases = sum(result.passed for result in results)
        residues = [result.residue for result in results if result.residue]
        all_passed = bool(results) and passed_cases == len(results)
        verdict = "D: demonstrated locally" if all_passed else "C: prototype with residues"
        if not results:
            verdict = "B: doctrine only — no executable cases"
            residues.append("No examples supplied; cannot promote beyond doctrine.")
        return OAKReport(
            state_name=state.name,
            verdict=verdict,
            passed=all_passed,
            total_cases=len(results),
            passed_cases=passed_cases,
            failed_cases=len(results) - passed_cases,
            residues=residues,
            case_results=results,
        )

    def _run_case(self, state: SoftwareState, case: ExampleCase) -> CaseResult:
        input_checks = state.contract.check_inputs(case.args, dict(case.kwargs))
        if not all_checks_passed(input_checks):
            return CaseResult(
                name=case.name,
                passed=False,
                input_checks=input_checks,
                residue="Input contract failed before execution.",
            )

        try:
            output = state.target(*case.args, **case.kwargs)
        except BaseException as exc:  # intentionally catches callable failures as residues
            exception_checks = state.contract.check_exception(exc)
            expected_exception_ok = case.expect_exception is not None and isinstance(exc, case.expect_exception)
            passed = expected_exception_ok and all_checks_passed(exception_checks)
            return CaseResult(
                name=case.name,
                passed=passed,
                input_checks=input_checks,
                exception_checks=exception_checks,
                exception=f"{type(exc).__name__}: {exc}",
                residue=None if passed else "Unexpected or contract-invalid exception.",
            )

        output_checks = state.contract.check_output(output)
        expected_ok = case.expected is None or output == case.expected
        passed = expected_ok and all_checks_passed(output_checks) and case.expect_exception is None
        residue = None
        if case.expect_exception is not None:
            residue = f"Expected exception {case.expect_exception.__name__}, but returned {output!r}."
        elif not expected_ok:
            residue = f"Expected {case.expected!r}, got {output!r}."
        elif not all_checks_passed(output_checks):
            residue = "Output contract failed."
        return CaseResult(
            name=case.name,
            passed=passed,
            input_checks=input_checks,
            output_checks=output_checks,
            output=output,
            residue=residue,
        )


def _check_to_dict(check: ContractCheck) -> dict[str, Any]:
    return {"name": check.name, "passed": check.passed, "message": check.message}
