"""Omega Tensor Research Self-Model R0.8.

R0.8 learns *predictive software associations* from benchmark/research episodes.
It does not infer psychological traits, scientific truth, or causal operator
credit from observational history.

The layer is intentionally downstream of R0.7 Tensor DiscoveryBench and keeps
three memories:

- M+ : benchmark-useful evidence;
- M- : benchmark-negative evidence / anti-pattern;
- M? : unresolved or insufficiently discriminating evidence.

All credit and Value-of-Computation receipts are explicit policy proxies.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from statistics import mean
from typing import Iterable, Sequence

from sage_tristan.tensor_discovery_bench import (
    BenchmarkFamily,
    BenchmarkTask,
    SystemKind,
    deterministic_tasks,
    evaluate,
    system_profile,
)
from sage_tristan.tensor_research_compiler import LLMTRegistry, synthetic_tensor_fixture


EPS = 1e-12


class OutcomeClass(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class MemoryClass(str, Enum):
    M_PLUS = "M+"
    M_MINUS = "M-"
    M_QUESTION = "M?"


class CreditUnit(str, Enum):
    OPERATOR = "operator"
    COALITION = "coalition"
    SYSTEM_KIND = "system_kind"


@dataclass(frozen=True, slots=True)
class ResearchEpisode:
    episode_id: str
    problem_id: str
    family: BenchmarkFamily
    system_kind: SystemKind
    selected_person_ids: tuple[str, ...]
    operator_ids: tuple[str, ...]
    representation_ids: tuple[str, ...]
    information_gain_proxy: float
    declared_cost: float
    declared_risk: float
    calibration_proxy: float
    hidden_target: bool
    contamination_controlled: bool
    outcome: OutcomeClass
    memory_class: MemoryClass
    provenance_ids: tuple[str, ...]
    causal_intervention: bool = False
    external_scientific_validation: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("information_gain_proxy", self.information_gain_proxy),
            ("declared_risk", self.declared_risk),
            ("calibration_proxy", self.calibration_proxy),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.declared_cost <= 0:
            raise ValueError("declared_cost must be positive")
        if not self.provenance_ids:
            raise ValueError("research episode requires provenance")


@dataclass(frozen=True, slots=True)
class EpisodeLedger:
    episodes: tuple[ResearchEpisode, ...] = ()
    append_only: bool = True

    def __post_init__(self) -> None:
        ids = [item.episode_id for item in self.episodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate research episode id")
        if not self.append_only:
            raise ValueError("R0.8 episode ledger is append-only by contract")

    def append(self, episode: ResearchEpisode) -> "EpisodeLedger":
        if any(item.episode_id == episode.episode_id for item in self.episodes):
            raise ValueError(f"duplicate research episode id: {episode.episode_id}")
        return EpisodeLedger(self.episodes + (episode,))


@dataclass(frozen=True, slots=True)
class CreditReceipt:
    unit_type: CreditUnit
    unit_id: str
    support_count: int
    comparison_count: int
    mean_information_with_unit: float
    mean_information_without_unit: float
    association_delta: float
    mean_cost_with_unit: float
    causal_credit_proven: bool = False
    confounding_possible: bool = True
    observational_only: bool = True


@dataclass(frozen=True, slots=True)
class PredictionReceipt:
    problem_family: BenchmarkFamily
    system_kind: SystemKind
    support_count: int
    predicted_information_gain_proxy: float
    predicted_cost_proxy: float
    predicted_calibration_proxy: float
    predictive_association_only: bool = True
    causal_effect_proven: bool = False
    external_validity_proven: bool = False


@dataclass(frozen=True, slots=True)
class ValueOfComputationReceipt:
    candidate_id: str
    expected_information_gain_proxy: float
    expected_cost: float
    expected_risk: float
    uncertainty_penalty: float
    value_of_computation_proxy: float
    recommend_compute: bool
    policy_proxy_only: bool = True
    causal_effect_proven: bool = False
    guaranteed_positive_return: bool = False


@dataclass(frozen=True, slots=True)
class SelfModelReport:
    episode_count: int
    memory_counts: tuple[tuple[str, int], ...]
    operator_credits: tuple[CreditReceipt, ...]
    coalition_credits: tuple[CreditReceipt, ...]
    predictions: tuple[PredictionReceipt, ...]
    value_receipts: tuple[ValueOfComputationReceipt, ...]


def _memory_class(information: float, calibration: float) -> MemoryClass:
    if information >= 0.70 and calibration >= 0.65:
        return MemoryClass.M_PLUS
    if information <= 0.35:
        return MemoryClass.M_MINUS
    return MemoryClass.M_QUESTION


def _outcome(information: float) -> OutcomeClass:
    if information >= 0.70:
        return OutcomeClass.POSITIVE
    if information <= 0.35:
        return OutcomeClass.NEGATIVE
    return OutcomeClass.MIXED


def _episode_id(task: BenchmarkTask, system_kind: SystemKind, people: Sequence[str]) -> str:
    payload = json.dumps(
        {
            "task": task.task_id,
            "family": task.family.value,
            "system": system_kind.value,
            "people": tuple(people),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "episode_" + sha256(payload.encode("utf-8")).hexdigest()[:16]


def _profile_operators(registry: LLMTRegistry, people: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({op for person_id in people for op in registry.get(person_id).operator_ids}))


def _profile_representations(registry: LLMTRegistry, people: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({rep for person_id in people for rep in registry.get(person_id).representation_ids}))


def deterministic_episode_ledger() -> EpisodeLedger:
    """Convert the 8x4 R0.7 deterministic benchmark surface into 32 episodes."""
    registry, _ = synthetic_tensor_fixture()
    ledger = EpisodeLedger()
    for task in deterministic_tasks():
        for kind in SystemKind:
            profile = system_profile(kind, task, registry)
            run = evaluate(task, profile)
            risk = min(1.0, sum(registry.get(pid).risk for pid in profile.selected_person_ids))
            contamination_controlled = all(
                getattr(task.contamination, axis).value == "controlled_zero"
                for axis in ("context", "retrieval", "tools", "pretraining", "benchmark", "human")
            )
            episode = ResearchEpisode(
                episode_id=_episode_id(task, kind, profile.selected_person_ids),
                problem_id=task.task_id,
                family=task.family,
                system_kind=kind,
                selected_person_ids=profile.selected_person_ids,
                operator_ids=_profile_operators(registry, profile.selected_person_ids),
                representation_ids=_profile_representations(registry, profile.selected_person_ids),
                information_gain_proxy=run.verified_information_gain_proxy,
                declared_cost=run.declared_cost,
                declared_risk=round(risk, 6),
                calibration_proxy=run.calibration_proxy,
                hidden_target=task.hidden_target,
                contamination_controlled=contamination_controlled,
                outcome=_outcome(run.verified_information_gain_proxy),
                memory_class=_memory_class(run.verified_information_gain_proxy, run.calibration_proxy),
                provenance_ids=("tensor_discovery_bench_r07", task.task_id),
            )
            ledger = ledger.append(episode)
    return ledger


def _contains_unit(episode: ResearchEpisode, unit_type: CreditUnit, unit_id: str) -> bool:
    if unit_type is CreditUnit.OPERATOR:
        return unit_id in episode.operator_ids
    if unit_type is CreditUnit.COALITION:
        return "+".join(sorted(episode.selected_person_ids)) == unit_id
    if unit_type is CreditUnit.SYSTEM_KIND:
        return episode.system_kind.value == unit_id
    raise ValueError(unit_type)


def credit_receipt(
    episodes: Sequence[ResearchEpisode],
    unit_type: CreditUnit,
    unit_id: str,
) -> CreditReceipt:
    with_unit = [item for item in episodes if _contains_unit(item, unit_type, unit_id)]
    without_unit = [item for item in episodes if not _contains_unit(item, unit_type, unit_id)]
    if not with_unit:
        return CreditReceipt(unit_type, unit_id, 0, len(without_unit), 0.0, round(mean(item.information_gain_proxy for item in without_unit), 6) if without_unit else 0.0, 0.0, 0.0)
    mean_with = mean(item.information_gain_proxy for item in with_unit)
    mean_without = mean(item.information_gain_proxy for item in without_unit) if without_unit else 0.0
    mean_cost = mean(item.declared_cost for item in with_unit)
    return CreditReceipt(
        unit_type=unit_type,
        unit_id=unit_id,
        support_count=len(with_unit),
        comparison_count=len(without_unit),
        mean_information_with_unit=round(mean_with, 6),
        mean_information_without_unit=round(mean_without, 6),
        association_delta=round(mean_with - mean_without, 6),
        mean_cost_with_unit=round(mean_cost, 6),
    )


def predict(
    episodes: Sequence[ResearchEpisode],
    family: BenchmarkFamily,
    system_kind: SystemKind,
) -> PredictionReceipt:
    matches = [item for item in episodes if item.family is family and item.system_kind is system_kind]
    if not matches:
        return PredictionReceipt(family, system_kind, 0, 0.0, 0.0, 0.0)
    return PredictionReceipt(
        problem_family=family,
        system_kind=system_kind,
        support_count=len(matches),
        predicted_information_gain_proxy=round(mean(item.information_gain_proxy for item in matches), 6),
        predicted_cost_proxy=round(mean(item.declared_cost for item in matches), 6),
        predicted_calibration_proxy=round(mean(item.calibration_proxy for item in matches), 6),
    )


def value_of_computation(
    candidate_id: str,
    *,
    expected_information_gain_proxy: float,
    expected_cost: float,
    expected_risk: float,
    uncertainty: float,
    risk_weight: float = 0.50,
    uncertainty_weight: float = 0.35,
) -> ValueOfComputationReceipt:
    for name, value in (
        ("expected_information_gain_proxy", expected_information_gain_proxy),
        ("expected_risk", expected_risk),
        ("uncertainty", uncertainty),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")
    if expected_cost < 0:
        raise ValueError("expected_cost must be non-negative")
    uncertainty_penalty = uncertainty_weight * uncertainty
    value = expected_information_gain_proxy - expected_cost - risk_weight * expected_risk - uncertainty_penalty
    return ValueOfComputationReceipt(
        candidate_id=candidate_id,
        expected_information_gain_proxy=expected_information_gain_proxy,
        expected_cost=expected_cost,
        expected_risk=expected_risk,
        uncertainty_penalty=round(uncertainty_penalty, 6),
        value_of_computation_proxy=round(value, 6),
        recommend_compute=value > 0,
    )


def build_self_model(ledger: EpisodeLedger | None = None) -> SelfModelReport:
    ledger = ledger or deterministic_episode_ledger()
    episodes = ledger.episodes
    operators = tuple(sorted({op for item in episodes for op in item.operator_ids}))
    coalitions = tuple(sorted({"+".join(sorted(item.selected_person_ids)) for item in episodes}))
    operator_credits = tuple(credit_receipt(episodes, CreditUnit.OPERATOR, op) for op in operators)
    coalition_credits = tuple(credit_receipt(episodes, CreditUnit.COALITION, coalition) for coalition in coalitions)
    predictions = tuple(
        predict(episodes, family, kind)
        for family in BenchmarkFamily
        for kind in SystemKind
    )
    memories = tuple(
        (memory.value, sum(item.memory_class is memory for item in episodes))
        for memory in MemoryClass
    )
    # Two explicit policy probes: one cheap and one deliberately expensive.
    value_receipts = (
        value_of_computation(
            "cheap_followup",
            expected_information_gain_proxy=0.72,
            expected_cost=0.18,
            expected_risk=0.08,
            uncertainty=0.20,
        ),
        value_of_computation(
            "expensive_followup",
            expected_information_gain_proxy=0.45,
            expected_cost=0.55,
            expected_risk=0.20,
            uncertainty=0.40,
        ),
    )
    return SelfModelReport(
        episode_count=len(episodes),
        memory_counts=memories,
        operator_credits=operator_credits,
        coalition_credits=coalition_credits,
        predictions=predictions,
        value_receipts=value_receipts,
    )


def compile_report() -> dict[str, object]:
    ledger = deterministic_episode_ledger()
    model = build_self_model(ledger)
    return {
        "engine": "Omega-TENSOR-RESEARCH-SELF-MODEL-T",
        "release": "R0.8",
        "episode_count": model.episode_count,
        "memory_counts": dict(model.memory_counts),
        "operator_credits": [asdict(item) for item in model.operator_credits],
        "coalition_credits": [asdict(item) for item in model.coalition_credits],
        "predictions": [asdict(item) for item in model.predictions],
        "value_of_computation": [asdict(item) for item in model.value_receipts],
        "append_only_episode_ledger": True,
        "m_plus_is_truth": False,
        "m_minus_is_permanent_refutation": False,
        "m_question_preserved": True,
        "credit_is_causal_proof": False,
        "prediction_is_causal_effect": False,
        "value_of_computation_is_guaranteed_return": False,
        "benchmark_history_is_external_scientific_validation": False,
        "upstream_r07_required": True,
        "oak_note": (
            "R0.8 learns predictive benchmark associations and policy proxies from R0.7 episodes. "
            "Observational credit is not causal credit; benchmark history is not external scientific validation; "
            "Value of Computation is a decision proxy, not a guaranteed return."
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
    parser = argparse.ArgumentParser(description="Tensor Research Self-Model R0.8")
    parser.add_argument("--report", action="store_true")
    parser.parse_args(argv)
    print(json.dumps(_jsonable(compile_report()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
