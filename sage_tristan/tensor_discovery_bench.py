"""Omega Tensor DiscoveryBench R0.7.

R0.7 evaluates the software architecture introduced in R0.6 without claiming a
scalar intelligence score, human novelty, independent discovery, or causal
operator effectiveness. The deterministic fixtures in this module are
benchmark proxies used to validate the benchmark harness itself.

The central comparison unit is: same task + same declared evidence boundary +
multiple system configurations. Performance, resource cost, contamination,
calibration, robustness and ablation effects remain separate fields.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
import json
from statistics import mean
from typing import Mapping, Sequence

from sage_tristan.tensor_research_compiler import (
    CognitiveProgram,
    LLMTRegistry,
    ceres_cognitive_program,
    synthetic_tensor_fixture,
)
from sage_tristan.tensor_risk_gate import CumulativeRiskTensorCompiler


EPS = 1e-12


class BenchmarkFamily(str, Enum):
    HISTORICAL = "historical"
    SYNTHETIC = "synthetic"
    SECRET = "secret"
    DYNAMIC = "dynamic"
    FORMAL = "formal"
    SIMULATION = "simulation"
    CROSS_DOMAIN = "cross_domain"
    ADVERSARIAL = "adversarial"


class SystemKind(str, Enum):
    SINGLE_LLMT = "single_llmt"
    SINGLE_SHADOW = "single_shadow"
    FIXED_COALITION = "fixed_coalition"
    META_LLMT = "meta_llmt"


class ExposureStatus(str, Enum):
    CONTROLLED_ZERO = "controlled_zero"
    POSSIBLE = "possible"
    PRESENT = "present"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ContaminationTensor:
    context: ExposureStatus
    retrieval: ExposureStatus
    tools: ExposureStatus
    pretraining: ExposureStatus
    benchmark: ExposureStatus
    human: ExposureStatus

    @property
    def independent_discovery_eligible(self) -> bool:
        return all(value is ExposureStatus.CONTROLLED_ZERO for value in (
            self.context,
            self.retrieval,
            self.tools,
            self.pretraining,
            self.benchmark,
            self.human,
        ))

    @property
    def uncertain_axes(self) -> tuple[str, ...]:
        values = asdict(self)
        return tuple(sorted(key for key, value in values.items() if value in {ExposureStatus.POSSIBLE, ExposureStatus.UNKNOWN}))


@dataclass(frozen=True, slots=True)
class BenchmarkTask:
    task_id: str
    family: BenchmarkFamily
    required_capabilities: tuple[str, ...]
    contamination: ContaminationTensor
    budget: float
    hidden_target: bool
    novelty_scope: str = "benchmark_only"
    human_novelty_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.required_capabilities:
            raise ValueError("benchmark task requires capabilities")
        if self.budget <= 0:
            raise ValueError("benchmark budget must be positive")
        if self.human_novelty_claimed:
            raise ValueError("R0.7 fixtures cannot claim human novelty")


@dataclass(frozen=True, slots=True)
class SystemProfile:
    system_id: str
    kind: SystemKind
    selected_person_ids: tuple[str, ...]
    capability_tags: tuple[str, ...]
    source_ids: tuple[str, ...]
    declared_cost: float
    shadow_count: int
    adaptive_routing: bool

    def __post_init__(self) -> None:
        if self.declared_cost <= 0:
            raise ValueError("system cost must be positive")
        if self.shadow_count < 0:
            raise ValueError("shadow_count must be non-negative")


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    task_id: str
    family: BenchmarkFamily
    system_id: str
    system_kind: SystemKind
    capability_coverage: float
    evidence_strength: float
    calibration_proxy: float
    robustness_proxy: float
    verified_information_gain_proxy: float
    declared_cost: float
    discovery_yield: float
    contamination: ContaminationTensor
    independent_discovery_eligible: bool
    independent_discovery_claimed: bool = False
    human_novelty_claimed: bool = False
    benchmark_proxy_only: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("capability_coverage", self.capability_coverage),
            ("evidence_strength", self.evidence_strength),
            ("calibration_proxy", self.calibration_proxy),
            ("robustness_proxy", self.robustness_proxy),
            ("verified_information_gain_proxy", self.verified_information_gain_proxy),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.declared_cost <= 0:
            raise ValueError("declared_cost must be positive")
        if self.independent_discovery_claimed:
            raise ValueError("R0.7 benchmark harness does not certify independent discovery")
        if self.human_novelty_claimed:
            raise ValueError("R0.7 benchmark harness does not certify human novelty")


@dataclass(frozen=True, slots=True)
class SuiteSummary:
    system_id: str
    system_kind: SystemKind
    mean_coverage: float
    mean_evidence_strength: float
    mean_calibration: float
    mean_robustness: float
    total_information_gain_proxy: float
    total_cost: float
    cost_normalized_yield: float


@dataclass(frozen=True, slots=True)
class AblationReceipt:
    program_id: str
    removed_instruction_id: str
    removed_operator_id: str | None
    baseline_capability_coverage: float
    ablated_capability_coverage: float
    delta_coverage: float
    causal_effect_proven: bool = False


@dataclass(frozen=True, slots=True)
class ParetoReceipt:
    task_id: str
    frontier_system_ids: tuple[str, ...]
    scalar_intelligence_score_produced: bool = False


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    runs: tuple[BenchmarkRun, ...]
    summaries: tuple[SuiteSummary, ...]
    pareto: tuple[ParetoReceipt, ...]
    ablations: tuple[AblationReceipt, ...]


def default_contamination(family: BenchmarkFamily) -> ContaminationTensor:
    if family is BenchmarkFamily.HISTORICAL:
        return ContaminationTensor(
            context=ExposureStatus.CONTROLLED_ZERO,
            retrieval=ExposureStatus.CONTROLLED_ZERO,
            tools=ExposureStatus.CONTROLLED_ZERO,
            pretraining=ExposureStatus.POSSIBLE,
            benchmark=ExposureStatus.POSSIBLE,
            human=ExposureStatus.UNKNOWN,
        )
    if family is BenchmarkFamily.SECRET:
        return ContaminationTensor(
            context=ExposureStatus.CONTROLLED_ZERO,
            retrieval=ExposureStatus.CONTROLLED_ZERO,
            tools=ExposureStatus.CONTROLLED_ZERO,
            pretraining=ExposureStatus.UNKNOWN,
            benchmark=ExposureStatus.CONTROLLED_ZERO,
            human=ExposureStatus.CONTROLLED_ZERO,
        )
    return ContaminationTensor(*((ExposureStatus.CONTROLLED_ZERO,) * 6))


def deterministic_tasks() -> tuple[BenchmarkTask, ...]:
    families = tuple(BenchmarkFamily)
    requirements = (
        ("representation_switch", "invariant_search"),
        ("representation_switch", "residual_control"),
        ("residual_control", "counterexample"),
        ("representation_switch",),
        ("invariant_search", "counterexample"),
        ("residual_control",),
        ("representation_switch", "counterexample"),
        ("representation_switch", "invariant_search", "residual_control"),
    )
    return tuple(
        BenchmarkTask(
            task_id=f"r07_{family.value}",
            family=family,
            required_capabilities=requirements[index],
            contamination=default_contamination(family),
            budget=1.0,
            hidden_target=family in {BenchmarkFamily.SECRET, BenchmarkFamily.SYNTHETIC, BenchmarkFamily.SIMULATION},
        )
        for index, family in enumerate(families)
    )


def _merge_people(registry: LLMTRegistry, person_ids: Sequence[str]) -> tuple[tuple[str, ...], tuple[str, ...], float]:
    people = tuple(registry.get(person_id) for person_id in person_ids)
    capabilities = tuple(sorted({cap for person in people for cap in person.capability_tags}))
    sources = tuple(sorted({source for person in people for source in person.source_ids}))
    cost = sum(person.cost for person in people)
    return capabilities, sources, cost


def system_profile(kind: SystemKind, task: BenchmarkTask, registry: LLMTRegistry) -> SystemProfile:
    if kind is SystemKind.SINGLE_LLMT:
        ids = ("person_a",)
        capabilities, sources, cost = _merge_people(registry, ids)
        return SystemProfile("single_llmt_a", kind, ids, capabilities, sources, cost, 0, False)
    if kind is SystemKind.SINGLE_SHADOW:
        ids = ("person_b",)
        capabilities, sources, cost = _merge_people(registry, ids)
        return SystemProfile("single_shadow_b", kind, ids, capabilities, sources, cost + 0.03, 1, False)
    if kind is SystemKind.FIXED_COALITION:
        ids = ("person_a", "person_b")
        capabilities, sources, cost = _merge_people(registry, ids)
        return SystemProfile("fixed_a_b", kind, ids, capabilities, sources, cost + 0.04, 2, False)

    problem_registry, _ = synthetic_tensor_fixture()
    from sage_tristan.tensor_research_compiler import ProblemGenome

    problem = ProblemGenome(
        problem_id=task.task_id,
        capability_tags=task.required_capabilities,
        domain_tags=(task.family.value,),
        initial_representation_ids=("native",),
        target_representation_ids=("target",),
        evidence_ids=("r07_fixture",),
        risk_budget=0.5,
    )
    receipt = CumulativeRiskTensorCompiler(problem_registry).compile(problem, max_llmts=3)
    ids = receipt.selected_person_ids
    capabilities, sources, cost = _merge_people(problem_registry, ids)
    return SystemProfile("meta_llmt_router", kind, ids, capabilities, sources, cost + 0.08, len(ids), True)


def evaluate(task: BenchmarkTask, profile: SystemProfile) -> BenchmarkRun:
    required = set(task.required_capabilities)
    capabilities = set(profile.capability_tags)
    coverage = len(required & capabilities) / len(required)
    evidence = min(1.0, len(profile.source_ids) / 5.0)
    calibration = min(1.0, 0.45 + 0.25 * coverage + 0.05 * min(2, len(profile.selected_person_ids)))
    robustness = min(1.0, 0.40 + 0.30 * coverage + 0.05 * min(3, profile.shadow_count))
    information = min(1.0, coverage * (0.65 + 0.35 * evidence))
    yield_value = information / max(EPS, profile.declared_cost)
    return BenchmarkRun(
        task_id=task.task_id,
        family=task.family,
        system_id=profile.system_id,
        system_kind=profile.kind,
        capability_coverage=round(coverage, 6),
        evidence_strength=round(evidence, 6),
        calibration_proxy=round(calibration, 6),
        robustness_proxy=round(robustness, 6),
        verified_information_gain_proxy=round(information, 6),
        declared_cost=round(profile.declared_cost, 6),
        discovery_yield=round(yield_value, 6),
        contamination=task.contamination,
        independent_discovery_eligible=task.hidden_target and task.contamination.independent_discovery_eligible,
    )


def summarize(runs: Sequence[BenchmarkRun]) -> SuiteSummary:
    if not runs:
        raise ValueError("cannot summarize empty run set")
    first = runs[0]
    if any(run.system_id != first.system_id for run in runs):
        raise ValueError("summary requires one system")
    total_information = sum(run.verified_information_gain_proxy for run in runs)
    total_cost = sum(run.declared_cost for run in runs)
    return SuiteSummary(
        system_id=first.system_id,
        system_kind=first.system_kind,
        mean_coverage=round(mean(run.capability_coverage for run in runs), 6),
        mean_evidence_strength=round(mean(run.evidence_strength for run in runs), 6),
        mean_calibration=round(mean(run.calibration_proxy for run in runs), 6),
        mean_robustness=round(mean(run.robustness_proxy for run in runs), 6),
        total_information_gain_proxy=round(total_information, 6),
        total_cost=round(total_cost, 6),
        cost_normalized_yield=round(total_information / max(EPS, total_cost), 6),
    )


def _dominates(left: BenchmarkRun, right: BenchmarkRun) -> bool:
    quality_left = (
        left.capability_coverage,
        left.evidence_strength,
        left.calibration_proxy,
        left.robustness_proxy,
        left.verified_information_gain_proxy,
    )
    quality_right = (
        right.capability_coverage,
        right.evidence_strength,
        right.calibration_proxy,
        right.robustness_proxy,
        right.verified_information_gain_proxy,
    )
    no_worse = all(a >= b for a, b in zip(quality_left, quality_right)) and left.declared_cost <= right.declared_cost
    strictly_better = any(a > b for a, b in zip(quality_left, quality_right)) or left.declared_cost < right.declared_cost
    return no_worse and strictly_better


def pareto_front(task_id: str, runs: Sequence[BenchmarkRun]) -> ParetoReceipt:
    candidates = [run for run in runs if run.task_id == task_id]
    frontier = [
        candidate.system_id
        for candidate in candidates
        if not any(_dominates(other, candidate) for other in candidates if other.system_id != candidate.system_id)
    ]
    return ParetoReceipt(task_id, tuple(sorted(frontier)))


def ablate_program(program: CognitiveProgram) -> tuple[AblationReceipt, ...]:
    operators = tuple(item for item in program.instructions if item.operator_id)
    baseline_ids = {item.operator_id for item in operators if item.operator_id}
    if not baseline_ids:
        return ()
    receipts = []
    for instruction in operators:
        remaining = baseline_ids - ({instruction.operator_id} if instruction.operator_id else set())
        baseline_coverage = 1.0
        ablated = len(remaining) / len(baseline_ids)
        receipts.append(
            AblationReceipt(
                program_id=program.program_id,
                removed_instruction_id=instruction.instruction_id,
                removed_operator_id=instruction.operator_id,
                baseline_capability_coverage=baseline_coverage,
                ablated_capability_coverage=round(ablated, 6),
                delta_coverage=round(baseline_coverage - ablated, 6),
            )
        )
    return tuple(receipts)


def build_benchmark_report() -> BenchmarkReport:
    registry, _ = synthetic_tensor_fixture()
    tasks = deterministic_tasks()
    runs = tuple(
        evaluate(task, system_profile(kind, task, registry))
        for task in tasks
        for kind in SystemKind
    )
    summaries = tuple(
        summarize(tuple(run for run in runs if run.system_kind is kind))
        for kind in SystemKind
    )
    pareto = tuple(pareto_front(task.task_id, runs) for task in tasks)
    ablations = ablate_program(ceres_cognitive_program())
    return BenchmarkReport(runs, summaries, pareto, ablations)


def compile_report() -> dict[str, object]:
    report = build_benchmark_report()
    historical = next(task for task in deterministic_tasks() if task.family is BenchmarkFamily.HISTORICAL)
    systems = tuple(kind.value for kind in SystemKind)
    summary_by_kind: Mapping[SystemKind, SuiteSummary] = {item.system_kind: item for item in report.summaries}
    meta = summary_by_kind[SystemKind.META_LLMT]
    best_yield = max(item.cost_normalized_yield for item in report.summaries)
    return {
        "engine": "Omega-TENSOR-DISCOVERYBENCH-T",
        "release": "R0.7",
        "task_families": [item.value for item in BenchmarkFamily],
        "system_kinds": list(systems),
        "runs": [asdict(item) for item in report.runs],
        "suite_summaries": [asdict(item) for item in report.summaries],
        "pareto_fronts": [asdict(item) for item in report.pareto],
        "ablations": [asdict(item) for item in report.ablations],
        "historical_contamination": asdict(historical.contamination),
        "historical_independent_discovery_eligible": historical.hidden_target and historical.contamination.independent_discovery_eligible,
        "same_task_comparison": True,
        "all_baselines_retained": True,
        "cost_normalization_present": True,
        "contamination_tensor_separate_from_quality": True,
        "hidden_target_required_for_independent_discovery_eligibility": True,
        "meta_routing_uses_cumulative_risk_gate": True,
        "scalar_intelligence_score_produced": False,
        "human_novelty_claimed": False,
        "independent_discovery_certified": False,
        "meta_llmt_automatically_superior": False,
        "meta_is_best_yield_in_fixture": meta.cost_normalized_yield == best_yield,
        "ablation_is_causal_proof": False,
        "benchmark_proxy_only": True,
        "oak_note": (
            "R0.7 validates benchmark plumbing and comparison semantics using deterministic synthetic proxies. "
            "It does not measure human-like intelligence, certify novelty, remove pretrained-model contamination, "
            "or prove causal effects from ablations or coalition synergies. Independent-discovery eligibility also "
            "requires a hidden target in addition to controlled contamination axes. MetaLLMT routing uses the "
            "R0.6.1 additive cumulative declared-risk gate, which is not a real-world safety model."
        ),
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Tensor DiscoveryBench R0.7")
    parser.add_argument("--report", action="store_true")
    parser.parse_args(argv)
    print(json.dumps(_jsonable(compile_report()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
