"""GreatSagesBench R0.2 — deterministic benchmark/task compiler.

The benchmark does not grade mathematical genius from prose.  It audits
preconditions for serious rediscovery experiments: causal leakage, provenance,
epistemic typing, representation choice, operator programs and transfer claims.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import Iterable, Sequence

from sage_tristan.greatsages import ClaimClass, Discovery, SageProfile, discovery_by_id, get_profile
from sage_tristan.greatsages_time_machine import (
    CognitiveOperator,
    OperatorProgram,
    causal_leakage_firewall,
    compile_operator_program,
    epistemic_debt_for_discovery,
    genome_from_discovery,
    knowledge_field,
    minimal_discovery_set,
    operator_registry,
    structural_transfer_candidates,
)


class BenchmarkTask(str, Enum):
    REDISCOVER = "rediscover"
    PREDICT_NEXT_CONCEPT = "predict_next_concept"
    SELECT_REPRESENTATION = "select_representation"
    FIND_INVARIANT = "find_invariant"
    GENERATE_COUNTEREXAMPLE = "generate_counterexample"
    TRANSFER_DOMAIN = "transfer_domain"
    IDENTIFY_ANACHRONISM = "identify_anachronism"
    SEPARATE_EVIDENCE_INTERPRETATION = "separate_evidence_interpretation"


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    sage_id: str
    discovery_id: str
    gate_year: int
    task: BenchmarkTask
    visible_discovery_ids: tuple[str, ...]
    masked_discovery_ids: tuple[str, ...]
    prerequisite_ids: tuple[str, ...]
    target_withheld: bool
    required_claim_separation: tuple[str, ...]
    scoring_axes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkReceipt:
    case_id: str
    leakage_free: bool
    provenance_present: bool
    claim_separation_explicit: bool
    target_withheld: bool
    epistemic_debt_score: float
    status: str
    failures: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LearningPath:
    discovery_id: str
    prerequisite_discovery_ids: tuple[str, ...]
    questions: tuple[str, ...]
    final_challenge: str
    claim_class: ClaimClass = ClaimClass.RECONSTRUCTION


@dataclass(frozen=True, slots=True)
class RouterCandidate:
    operator_id: str
    match_score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MetaSagePlan:
    problem_tags: tuple[str, ...]
    selected_operator_ids: tuple[str, ...]
    adversarial_operator_ids: tuple[str, ...]
    program: OperatorProgram
    stop_conditions: tuple[str, ...]
    oak_requirements: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WhiteSpaceCell:
    transformation: str
    domain: str
    observed_count: int
    status: str


@dataclass(frozen=True, slots=True)
class NegativeKnowledgeRecord:
    record_id: str
    claim: str
    why_plausible: str
    why_failed: str
    detection_method: str
    transferable_lesson: str
    claim_class: ClaimClass = ClaimClass.RECONSTRUCTION


@dataclass(frozen=True, slots=True)
class ScienceFossil:
    fossil_id: str
    historical_claim: str
    historical_status: str
    fertile_method: str
    reuse_hypothesis: str
    claim_class: ClaimClass = ClaimClass.FERTILE_HYPOTHESIS


TASK_AXES: dict[BenchmarkTask, tuple[str, ...]] = {
    BenchmarkTask.REDISCOVER: ("correctness", "leakage_control", "prerequisite_use", "provenance"),
    BenchmarkTask.PREDICT_NEXT_CONCEPT: ("historical_admissibility", "calibration", "alternative_paths"),
    BenchmarkTask.SELECT_REPRESENTATION: ("complexity_reduction", "invariant_preservation", "anachronism_control"),
    BenchmarkTask.FIND_INVARIANT: ("invariance_test", "counterexample_search", "compression"),
    BenchmarkTask.GENERATE_COUNTEREXAMPLE: ("attack_strength", "domain_validity", "negative_memory"),
    BenchmarkTask.TRANSFER_DOMAIN: ("structural_match", "analogy_limits", "baseline_comparison"),
    BenchmarkTask.IDENTIFY_ANACHRONISM: ("date_gate", "notation_gate", "instrument_gate", "language_gate"),
    BenchmarkTask.SEPARATE_EVIDENCE_INTERPRETATION: ("source_directness", "claim_typing", "uncertainty"),
}


def build_benchmark_case(profile: SageProfile, discovery_id: str, task: BenchmarkTask) -> BenchmarkCase:
    target = discovery_by_id(profile, discovery_id)
    gate_year = max(profile.birth_year, target.year - 1)
    firewall = causal_leakage_firewall(profile, discovery_id, year=gate_year)
    return BenchmarkCase(
        case_id=f"{profile.sage_id}::{discovery_id}::{task.value}",
        sage_id=profile.sage_id,
        discovery_id=discovery_id,
        gate_year=gate_year,
        task=task,
        visible_discovery_ids=firewall.visible_discovery_ids,
        masked_discovery_ids=firewall.masked_discovery_ids,
        prerequisite_ids=target.prerequisite_ids,
        target_withheld=firewall.target_masked,
        required_claim_separation=(
            "source_historical",
            "reconstruction",
            "cognitive_model",
            "counterfactual",
            "fertile_hypothesis",
        ),
        scoring_axes=TASK_AXES[task],
    )


def build_suite(profile: SageProfile, discovery_id: str) -> tuple[BenchmarkCase, ...]:
    return tuple(build_benchmark_case(profile, discovery_id, task) for task in BenchmarkTask)


def audit_case(profile: SageProfile, case: BenchmarkCase) -> BenchmarkReceipt:
    discovery = discovery_by_id(profile, case.discovery_id)
    failures: list[str] = []
    leakage_free = case.discovery_id in set(case.masked_discovery_ids) and not (
        set(case.visible_discovery_ids) & set(case.masked_discovery_ids)
    )
    if not leakage_free:
        failures.append("causal leakage firewall failed")
    provenance_present = bool(discovery.source_ids)
    if not provenance_present:
        failures.append("discovery lacks source identifiers")
    claim_separation_explicit = len(case.required_claim_separation) >= 5
    if not claim_separation_explicit:
        failures.append("epistemic classes are collapsed")
    if not case.target_withheld:
        failures.append("target discovery is visible")
    debt = epistemic_debt_for_discovery(profile, case.discovery_id).score
    status = "PROMOTE_SOFTWARE_BENCH" if not failures else "QUARANTINE"
    return BenchmarkReceipt(
        case_id=case.case_id,
        leakage_free=leakage_free,
        provenance_present=provenance_present,
        claim_separation_explicit=claim_separation_explicit,
        target_withheld=case.target_withheld,
        epistemic_debt_score=debt,
        status=status,
        failures=tuple(failures),
    )


def blind_tournament_pack(profile: SageProfile, discovery_id: str) -> dict[str, object]:
    """Compile an agent-neutral blind historical tournament pack.

    The pack contains only the gate, visible discoveries and evaluation
    contract.  It deliberately omits the discovery title, problem statement,
    compressed invariant and all post-gate descendants.
    """
    target = discovery_by_id(profile, discovery_id)
    case = build_benchmark_case(profile, discovery_id, BenchmarkTask.REDISCOVER)
    return {
        "tournament_id": f"blind::{profile.sage_id}::{discovery_id}",
        "sage_id": profile.sage_id,
        "gate_year": case.gate_year,
        "target_year": target.year,
        "target_id_hash": __import__("hashlib").sha256(discovery_id.encode("utf-8")).hexdigest(),
        "visible_discovery_ids": case.visible_discovery_ids,
        "masked_count": len(case.masked_discovery_ids),
        "scoring_axes": case.scoring_axes,
        "anti_leakage_rule": "target identity/content and all modeled descendants remain withheld from contestants",
        "historical_truth_certified": False,
    }


def learning_compiler(profile: SageProfile, discovery_id: str) -> LearningPath:
    target = discovery_by_id(profile, discovery_id)
    prerequisites = minimal_discovery_set(profile, discovery_id)
    questions = tuple(
        [f"What reusable invariant or representation was established by prerequisite {item}?" for item in prerequisites]
        + [
            "Which observations or constraints make the target problem identifiable?",
            "Which representation exposes the smallest sufficient structure without future knowledge?",
            "What counterexample would invalidate the proposed reconstruction?",
        ]
    )
    return LearningPath(
        discovery_id=discovery_id,
        prerequisite_discovery_ids=prerequisites,
        questions=questions,
        final_challenge=f"Reconstruct {target.title} from the gated prerequisite set, then separate history from reconstruction.",
    )


def _operator_tags(operator: CognitiveOperator) -> frozenset[str]:
    text = f"{operator.operator_id} {operator.label} {operator.action}".lower().replace("-", "_")
    return frozenset(token.strip(".,:;()") for token in text.split() if len(token.strip(".,:;()")) > 3)


def route_operators(profile: SageProfile, problem_tags: Iterable[str], *, top_k: int = 3) -> tuple[RouterCandidate, ...]:
    normalized = frozenset(tag.lower().replace("-", "_") for tag in problem_tags)
    candidates: list[RouterCandidate] = []
    for operator in operator_registry(profile).values():
        tags = _operator_tags(operator)
        overlap = normalized & tags
        semantic_bonus = 0.0
        if "inverse" in normalized and any(token in operator.operator_id for token in ("approximation", "residual", "representation")):
            semantic_bonus += 0.35
        if "geometry" in normalized and "invariant" in operator.operator_id:
            semantic_bonus += 0.35
        if "symmetry" in normalized and "symmetry" in operator.operator_id:
            semantic_bonus += 0.45
        if "adversarial" in normalized and operator.operator_id.startswith("anti_"):
            semantic_bonus += 0.5
        score = min(1.0, 0.15 * len(overlap) + semantic_bonus + 0.2 * operator.confidence)
        candidates.append(
            RouterCandidate(
                operator_id=operator.operator_id,
                match_score=round(score, 6),
                reasons=tuple(sorted(overlap)) or ("confidence_prior",),
            )
        )
    return tuple(sorted(candidates, key=lambda item: (-item.match_score, item.operator_id))[:top_k])


def meta_sage_plan(profile: SageProfile, problem_tags: Iterable[str], *, top_k: int = 3) -> MetaSagePlan:
    tags = tuple(sorted(set(tag.lower() for tag in problem_tags)))
    routed = route_operators(profile, tags, top_k=top_k)
    registry = operator_registry(profile)
    selected = tuple(item.operator_id for item in routed)
    adversaries = tuple(
        sorted(
            {
                registry[operator_id].counter_operator_id
                for operator_id in selected
                if registry[operator_id].counter_operator_id is not None
            }
        )
    )
    program = compile_operator_program(profile, selected or (next(iter(registry)),))
    return MetaSagePlan(
        problem_tags=tags,
        selected_operator_ids=selected,
        adversarial_operator_ids=adversaries,
        program=program,
        stop_conditions=(
            "no measurable gain over baseline after bounded operator trials",
            "epistemic debt increases without new evidence",
            "counterexample invalidates central invariant",
            "chronological or provenance gate fails",
        ),
        oak_requirements=(
            "retain baseline",
            "record residuals and failures",
            "label counterfactuals",
            "preserve source provenance",
            "do not promote novelty without external literature audit",
        ),
    )


def white_space_atlas(profile: SageProfile) -> tuple[WhiteSpaceCell, ...]:
    """Find sparse transformation × domain cells in the current finite seed.

    Empty cells are research prompts, not novelty claims.
    """
    transformations = ("representation_switch", "invariant_search", "approximation_residual", "symmetry_compression")
    domains = tuple(sorted({domain for item in profile.discoveries for domain in item.domains}))
    counts: Counter[tuple[str, str]] = Counter()
    operator_evidence = operator_registry(profile)
    discovery_domains = {item.discovery_id: item.domains for item in profile.discoveries}
    for transformation in transformations:
        operator = operator_evidence.get(transformation)
        if operator is None:
            continue
        for discovery_id in operator.evidence_discovery_ids:
            for domain in discovery_domains.get(discovery_id, ()):
                counts[(transformation, domain)] += 1
    cells = []
    for transformation in transformations:
        for domain in domains:
            count = counts[(transformation, domain)]
            cells.append(
                WhiteSpaceCell(
                    transformation=transformation,
                    domain=domain,
                    observed_count=count,
                    status="WHITE_SPACE_CANDIDATE" if count == 0 else "OBSERVED_IN_SEED",
                )
            )
    return tuple(sorted(cells, key=lambda item: (item.observed_count, item.transformation, item.domain)))


def unexplored_transfer_gaps(profile: SageProfile, source_discovery_id: str, *, threshold: float = 0.92) -> tuple[str, ...]:
    """Return weakly matched seed discoveries as prompts for cautious transfer.

    A large genome distance means the current structural encoding supplies weak
    evidence for transfer; such cells are gaps to investigate, not targets to
    claim as analogous.
    """
    return tuple(
        discovery_id
        for discovery_id, distance in structural_transfer_candidates(profile, source_discovery_id)
        if distance >= threshold
    )


def compile_bench_report(profile: SageProfile, discovery_id: str) -> dict[str, object]:
    suite = build_suite(profile, discovery_id)
    receipts = tuple(audit_case(profile, case) for case in suite)
    plan = meta_sage_plan(profile, discovery_by_id(profile, discovery_id).domains)
    field = knowledge_field(profile, max(profile.birth_year, discovery_by_id(profile, discovery_id).year - 1))
    return {
        "engine": "GreatSagesBench",
        "release": "R0.2",
        "sage_id": profile.sage_id,
        "discovery_id": discovery_id,
        "suite": tuple(asdict(case) for case in suite),
        "receipts": tuple(asdict(receipt) for receipt in receipts),
        "blind_tournament": blind_tournament_pack(profile, discovery_id),
        "learning_path": asdict(learning_compiler(profile, discovery_id)),
        "meta_sage_plan": asdict(plan),
        "knowledge_field_before_target": asdict(field),
        "white_space_top16": tuple(asdict(cell) for cell in white_space_atlas(profile)[:16]),
        "unexplored_transfer_gaps": unexplored_transfer_gaps(profile, discovery_id),
        "all_cases_promotable": all(receipt.status == "PROMOTE_SOFTWARE_BENCH" for receipt in receipts),
        "historical_truth_certified": False,
        "novelty_claimed_for_white_space": False,
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
    parser = argparse.ArgumentParser(description="GreatSagesBench R0.2")
    parser.add_argument("--sage", default="gauss")
    parser.add_argument("--discovery", default="gauss_1801_ceres")
    args = parser.parse_args(argv)
    profile = get_profile(args.sage)
    print(json.dumps(_jsonable(compile_bench_report(profile, args.discovery)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
