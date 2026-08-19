"""Contract primitives for Ω-CS-SOFTWARE-TRUTH.

A contract turns a line of code into a falsifiable behavioral hypothesis:
inputs must satisfy preconditions, outputs must satisfy postconditions, and
failures must be recorded as OAK residues instead of hidden assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class ContractCheck:
    """Result of a single contract predicate."""

    name: str
    passed: bool
    message: str = ""


@dataclass(frozen=True)
class Contract:
    """Executable input/output contract.

    The contract is intentionally simple and dependency-free. It can wrap any
    Python callable by evaluating named predicates against the input tuple,
    keyword mapping, output value, or raised exception.
    """

    name: str
    input_predicates: Mapping[str, Callable[[tuple[Any, ...], dict[str, Any]], bool]] = field(default_factory=dict)
    output_predicates: Mapping[str, Callable[[Any], bool]] = field(default_factory=dict)
    exception_predicates: Mapping[str, Callable[[BaseException], bool]] = field(default_factory=dict)

    def check_inputs(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[ContractCheck]:
        return _run_predicates(self.input_predicates, args, kwargs)

    def check_output(self, output: Any) -> list[ContractCheck]:
        return _run_predicates(self.output_predicates, output)

    def check_exception(self, exc: BaseException) -> list[ContractCheck]:
        if not self.exception_predicates:
            return [ContractCheck("unexpected_exception", False, f"{type(exc).__name__}: {exc}")]
        return _run_predicates(self.exception_predicates, exc)


def _run_predicates(predicates: Mapping[str, Callable[..., bool]], *payload: Any) -> list[ContractCheck]:
    checks: list[ContractCheck] = []
    for name, predicate in predicates.items():
        try:
            passed = bool(predicate(*payload))
            checks.append(ContractCheck(name=name, passed=passed))
        except Exception as exc:  # pragma: no cover - defensive residue capture
            checks.append(ContractCheck(name=name, passed=False, message=f"predicate_error: {type(exc).__name__}: {exc}"))
    return checks


def all_checks_passed(checks: Iterable[ContractCheck]) -> bool:
    """Return True only if every check passed."""

    return all(check.passed for check in checks)
