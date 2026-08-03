from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol


class Oracle(Protocol):
    oracle_id: str

    def evaluate(self, candidate: Callable[..., Any]) -> "OracleResult": ...


@dataclass(frozen=True)
class OracleResult:
    oracle_id: str
    passed: bool
    checks: int
    failures: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "oracle_id": self.oracle_id,
            "passed": self.passed,
            "checks": self.checks,
            "failures": list(self.failures),
        }


@dataclass(frozen=True)
class ExactCase:
    args: tuple[Any, ...]
    expected: Any
    name: str


@dataclass(frozen=True)
class ExactOracle:
    cases: tuple[ExactCase, ...]
    oracle_id: str = "oracle.exact"

    def evaluate(self, candidate: Callable[..., Any]) -> OracleResult:
        failures: list[str] = []
        for case in self.cases:
            try:
                observed = candidate(*case.args)
            except Exception as exc:
                failures.append(f"{case.name}:exception:{type(exc).__name__}:{exc}")
                continue
            if observed != case.expected:
                failures.append(
                    f"{case.name}:expected={case.expected!r}:observed={observed!r}"
                )
        return OracleResult(
            oracle_id=self.oracle_id,
            passed=not failures,
            checks=len(self.cases),
            failures=tuple(failures),
        )


@dataclass(frozen=True)
class PropertyCheck:
    name: str
    predicate: Callable[[Callable[..., Any]], bool]


@dataclass(frozen=True)
class PropertyOracle:
    properties: tuple[PropertyCheck, ...]
    oracle_id: str = "oracle.property"

    def evaluate(self, candidate: Callable[..., Any]) -> OracleResult:
        failures: list[str] = []
        for prop in self.properties:
            try:
                passed = bool(prop.predicate(candidate))
            except Exception as exc:
                failures.append(f"{prop.name}:exception:{type(exc).__name__}:{exc}")
                continue
            if not passed:
                failures.append(f"{prop.name}:false")
        return OracleResult(
            oracle_id=self.oracle_id,
            passed=not failures,
            checks=len(self.properties),
            failures=tuple(failures),
        )


@dataclass(frozen=True)
class OracleMeshResult:
    passed: bool
    results: tuple[OracleResult, ...]

    @property
    def checks(self) -> int:
        return sum(result.checks for result in self.results)

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "results": [result.to_dict() for result in self.results],
        }


class OracleMesh:
    def __init__(self, oracles: Iterable[Oracle]) -> None:
        self.oracles = tuple(oracles)
        if not self.oracles:
            raise ValueError("OracleMesh requires at least one oracle")

    def evaluate(self, candidate: Callable[..., Any]) -> OracleMeshResult:
        results = tuple(oracle.evaluate(candidate) for oracle in self.oracles)
        return OracleMeshResult(
            passed=all(result.passed for result in results),
            results=results,
        )
