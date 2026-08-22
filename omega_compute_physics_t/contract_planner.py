"""Generate reviewable benchmark-contract candidates from Stage A evidence.

The planner never marks a checkout trusted automatically. It binds repository,
commit, callable, fixture, axes and static risk evidence into a candidate that a
human or higher-level reviewed adapter can later approve.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .benchmark_contract import BenchmarkContract, BenchmarkRisk, InputAxis
from .fixture_registry import FixtureSpec
from .fleet_stage_a import StageABenchmarkSeed
from .risk_preflight import RiskPreflightReport


@dataclass(frozen=True)
class ContractPlan:
    contract: BenchmarkContract
    planning_notes: tuple[str, ...]
    status: str = "benchmark-contract-plan"
    oak_warning: str = (
        "Generated contracts are review candidates. The planner never establishes "
        "that the target callable is safe, pure, semantically valid or sandboxed."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract.certificate(),
            "planning_notes": list(self.planning_notes),
            "status": self.status,
            "oak_warning": self.oak_warning,
        }


def plan_contract(
    seed: StageABenchmarkSeed,
    *,
    commit_sha: str,
    fixture: FixtureSpec,
    axis_values: Mapping[str, Sequence[float]],
    risk_report: RiskPreflightReport | None = None,
    repeats: int = 5,
    warmups: int = 1,
    timeout_s: float = 10.0,
    max_cases: int = 128,
) -> ContractPlan:
    fixture_errors = fixture.validate()
    if fixture_errors:
        raise ValueError(f"fixture is not plannable: {fixture_errors}")
    missing = [name for name in fixture.axis_names if name not in axis_values]
    if missing:
        raise ValueError(f"axis values missing for fixture axes: {missing}")
    axes = tuple(
        InputAxis(
            name=name,
            values=tuple(float(value) for value in axis_values[name]),
            description=fixture.input_schema.get(name, ""),
        )
        for name in fixture.axis_names
    )
    risk = risk_report.risk if risk_report is not None else BenchmarkRisk()
    module_key = seed.module.replace("/", ".").removesuffix(".py")
    contract_id = (
        f"{seed.repository}@{commit_sha[:12]}::{module_key}::{seed.function}::{fixture.fixture_id}"
    )
    contract = BenchmarkContract(
        contract_id=contract_id,
        repository=seed.repository,
        commit_sha=commit_sha,
        module=module_key,
        callable_name=seed.function,
        axes=axes,
        fixture=fixture.fixture_id,
        repeats=repeats,
        warmups=warmups,
        timeout_s=timeout_s,
        max_cases=max_cases,
        trusted_checkout=False,
        risk=risk,
    )
    notes = [
        "trusted_checkout intentionally remains false until explicit review",
        f"Stage A priority score={seed.priority_score:.6g}",
        f"structural hint={seed.structural_scaling_candidate}",
    ]
    if risk_report is None:
        notes.append("no source-level risk report supplied; conservative manual review required")
    elif risk_report.findings:
        notes.append(f"static risk preflight produced {len(risk_report.findings)} finding(s)")
    else:
        notes.append("static risk preflight found no configured indicators; this is not a safety guarantee")
    return ContractPlan(contract=contract, planning_notes=tuple(notes))
