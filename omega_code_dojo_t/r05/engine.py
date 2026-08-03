from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..r04.families import FAMILY_BY_ID, solve
from ..r04.models import AttemptStatus
from ..r04.verifier import ExactFixtureVerifier
from .policy import (
    AccessRequest,
    Decision,
    NormalizedProblem,
    Normalizer,
    PLATFORMS,
    PlatformMode,
    PolicyGate,
    ProblemRef,
    Verdict,
    sha256_hex,
    stable_id,
)


_TAG_TO_FAMILY = {
    "array": "sum_array",
    "implementation": "sum_array",
    "counting": "count_even",
    "string": "balanced_parentheses",
    "stack": "balanced_parentheses",
    "number_theory": "gcd_pair",
    "mathematics": "prime_count",
    "prime": "prime_count",
    "graph": "connected_components",
    "graph_traversal": "connected_components",
    "shortest_path": "shortest_path",
    "interval": "merge_intervals",
    "sorting": "merge_intervals",
    "two_pointers": "two_sum_exists",
    "hashing": "two_sum_exists",
    "maximum_subarray": "max_subarray",
    "dynamic_programming": "lis_length",
    "lis": "lis_length",
    "coin_change": "coin_change_min",
    "dag": "dag_possible",
    "topological_sort": "dag_possible",
    "edit_distance": "edit_distance",
    "binary_search": "binary_search_first",
    "knapsack": "knapsack_01",
    "grid": "grid_max_path",
    "greedy": "knapsack_01",
    "general_problem_solving": "sum_array",
}
_FAMILY_CYCLE = tuple(dict.fromkeys(_TAG_TO_FAMILY.values()))
_SKILLS = (
    ("array", "implementation"),
    ("counting", "array"),
    ("string", "stack"),
    ("number_theory", "mathematics"),
    ("prime", "number_theory"),
    ("graph", "shortest_path"),
    ("graph", "graph_traversal"),
    ("interval", "sorting"),
    ("two_pointers", "hashing"),
    ("maximum_subarray", "dynamic_programming"),
    ("lis", "dynamic_programming"),
    ("coin_change", "dynamic_programming"),
    ("dag", "topological_sort"),
    ("edit_distance", "string"),
    ("binary_search", "sorting"),
    ("knapsack", "dynamic_programming"),
    ("grid", "dynamic_programming"),
)


@dataclass(frozen=True)
class MultiJudgePolicy:
    reference_budget: int = 512
    shadow_budget: int = 256
    max_attempts: int = 2
    permanent_total_cap: int | None = None

    def __post_init__(self) -> None:
        if self.reference_budget <= 0 or self.shadow_budget <= 0 or self.max_attempts <= 0:
            raise ValueError("budgets must be positive")
        if self.shadow_budget > self.reference_budget:
            raise ValueError("shadow_budget cannot exceed reference_budget")


@dataclass(frozen=True)
class Selection:
    problem: NormalizedProblem
    verdict: Verdict
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {"problem": self.problem.to_dict(), "verdict": self.verdict.to_dict(), "score": self.score}


@dataclass(frozen=True)
class Resolution:
    canonical_id: str
    platform_id: str
    external_id: str
    status: str
    shadow_family_id: str | None
    shadow_problem_id: str | None
    selected_strategy_id: str | None
    attempts: int
    counterexamples: tuple[str, ...]
    cost_units: int
    manual_submission_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "platform_id": self.platform_id,
            "external_id": self.external_id,
            "status": self.status,
            "shadow_family_id": self.shadow_family_id,
            "shadow_problem_id": self.shadow_problem_id,
            "selected_strategy_id": self.selected_strategy_id,
            "attempts": self.attempts,
            "counterexamples": list(self.counterexamples),
            "cost_units": self.cost_units,
            "manual_submission_required": self.manual_submission_required,
            "proof_obligations": [
                "shadow_problem_is_original_synthetic_fixture",
                "external_problem_statement_not_copied",
                "external_problem_not_claimed_solved",
                "manual_external_submission_required",
            ],
        }


@dataclass
class Planner:
    gate: PolicyGate = field(default_factory=PolicyGate)
    seen: set[str] = field(default_factory=set)
    platform_counts: Counter[str] = field(default_factory=Counter)
    mastery: dict[str, float] = field(default_factory=dict)
    uncertainty: dict[str, float] = field(default_factory=dict)

    def select(self, problems: Iterable[NormalizedProblem], limit: int) -> tuple[Selection, ...]:
        ranked = []
        for problem in problems:
            verdict = self.gate.evaluate(AccessRequest(problem.platform_id, PlatformMode.PRACTICE, problem.content_class))
            mean_mastery = sum(self.mastery.get(skill, 0.5) for skill in problem.skills) / len(problem.skills)
            mean_uncertainty = sum(self.uncertainty.get(skill, 0.288675) for skill in problem.skills) / len(problem.skills)
            weakness = 1.0 - mean_mastery
            novelty = 0.0 if problem.canonical_id in self.seen else 1.0
            diversity = 1.0 / (1.0 + self.platform_counts[problem.platform_id])
            transfer = _fraction("transfer", problem.platform_id, *problem.skills)
            cost = 0.15 + 0.85 * problem.difficulty
            risk = {Decision.ALLOW: 0.0, Decision.REVIEW: 0.55, Decision.BLOCK: 1.0}[verdict.decision]
            score = 1.0 * weakness + 0.8 * min(1.0, mean_uncertainty * 3) + 0.7 * novelty + 0.5 * diversity + 0.5 * transfer - 0.4 * cost - 1.2 * risk
            if problem.solved:
                score -= 0.8
            elif problem.attempted:
                score += 0.2
            ranked.append(Selection(problem, verdict, score))
        ranked.sort(key=lambda item: (item.verdict.decision is Decision.BLOCK, -item.score, item.problem.canonical_id))
        return tuple(ranked[:limit])

    def observe(self, selection: Selection, success: bool) -> None:
        self.seen.add(selection.problem.canonical_id)
        self.platform_counts[selection.problem.platform_id] += 1
        for skill in selection.problem.skills:
            previous = self.mastery.get(skill, 0.5)
            self.mastery[skill] = previous + 0.08 * ((1.0 if success else 0.0) - previous)
            self.uncertainty[skill] = max(0.01, self.uncertainty.get(skill, 0.288675) * 0.92)


@dataclass
class ShadowResolver:
    verifier: ExactFixtureVerifier = field(default_factory=ExactFixtureVerifier)

    def resolve(self, selection: Selection, max_attempts: int) -> Resolution:
        if selection.verdict.decision is Decision.BLOCK:
            return Resolution(selection.problem.canonical_id, selection.problem.platform_id, selection.problem.external_id, "blocked", None, None, None, 0, (), 0)
        family_id = self.family_for(selection.problem)
        family = FAMILY_BY_ID[family_id]
        seed = int(sha256_hex(selection.problem.canonical_id)[:16], 16) % (2**32)
        difficulty = 1 + min(31, int(round(selection.problem.difficulty * 31)))
        problem = family.generate(seed, difficulty)
        counterexamples, attempts, cost, selected = [], 0, 0, None
        for strategy in family.strategies[:max_attempts]:
            attempts += 1
            observed, exception = None, None
            try:
                observed = solve(strategy.strategy_id, problem.input_payload)
            except BaseException as exc:
                exception = exc
            result = self.verifier.verify(problem, strategy, observed_output=observed, exception=exception)
            cost += _size(problem.input_payload) * (2 if strategy.exact else 1)
            if result.counterexample_signature:
                counterexamples.append(result.counterexample_signature)
            if result.status is AttemptStatus.VERIFIED:
                selected = strategy.strategy_id
                break
        return Resolution(
            selection.problem.canonical_id,
            selection.problem.platform_id,
            selection.problem.external_id,
            "shadow_solved" if selected else "shadow_unresolved",
            family_id,
            problem.problem_id,
            selected,
            attempts,
            tuple(counterexamples),
            cost,
        )

    def family_for(self, problem: NormalizedProblem) -> str:
        for skill in problem.skills:
            if skill in _TAG_TO_FAMILY:
                return _TAG_TO_FAMILY[skill]
        return _FAMILY_CYCLE[int(sha256_hex(problem.canonical_id)[:8], 16) % len(_FAMILY_CYCLE)]


@dataclass
class MultiJudgeEngine:
    normalizer: Normalizer = field(default_factory=Normalizer)
    planner: Planner = field(default_factory=Planner)
    resolver: ShadowResolver = field(default_factory=ShadowResolver)

    @property
    def logical_reference_space(self) -> int:
        return len(PLATFORMS) * (2**32) * 32

    def run(self, references: tuple[ProblemRef | dict[str, Any], ...], policy: MultiJudgePolicy) -> dict[str, Any]:
        normalized = self.normalizer.normalize(references)
        selections = self.planner.select(normalized, min(policy.reference_budget, len(normalized)))
        resolutions = []
        for selection in selections:
            if len(resolutions) >= policy.shadow_budget:
                resolutions.append(Resolution(selection.problem.canonical_id, selection.problem.platform_id, selection.problem.external_id, "blocked" if selection.verdict.decision is Decision.BLOCK else "reference_queued", None, None, None, 0, (), 0))
                continue
            if policy.permanent_total_cap is not None and len(resolutions) >= policy.permanent_total_cap:
                break
            result = self.resolver.resolve(selection, policy.max_attempts)
            resolutions.append(result)
            if result.status in {"shadow_solved", "shadow_unresolved"}:
                self.planner.observe(selection, result.status == "shadow_solved")

        metrics = []
        for platform in sorted(item.platform_id for item in PLATFORMS):
            platform_resolutions = [item for item in resolutions if item.platform_id == platform]
            metrics.append({
                "platform_id": platform,
                "discovered": sum(item.platform_id == platform for item in normalized),
                "selected": sum(item.problem.platform_id == platform for item in selections),
                "shadow_solved": sum(item.status == "shadow_solved" for item in platform_resolutions),
                "shadow_unresolved": sum(item.status == "shadow_unresolved" for item in platform_resolutions),
                "blocked": sum(item.status == "blocked" for item in platform_resolutions),
                "manual_submission_required": len(platform_resolutions),
            })
        solved = sum(item.status == "shadow_solved" for item in resolutions)
        unresolved = sum(item.status == "shadow_unresolved" for item in resolutions)
        materialized = solved + unresolved
        blocked = sum(item.verdict.decision is Decision.BLOCK for item in selections)
        receipt = {
            "campaign_id": stable_id("multijudge", [selection.problem.canonical_id for selection in selections]),
            "system_version": "R0.5",
            "platform_count": len(PLATFORMS),
            "logical_reference_space": self.logical_reference_space,
            "discovered_references": len(references),
            "normalized_references": len(normalized),
            "selected_references": len(selections),
            "materialized_shadow_problems": materialized,
            "solved_shadow_problems": solved,
            "unresolved_shadow_problems": unresolved,
            "shadow_solve_rate": solved / materialized if materialized else 0.0,
            "blocked_references": blocked,
            "total_cost_units": sum(item.cost_units for item in resolutions),
            "permanent_total_cap": policy.permanent_total_cap,
            "platform_metrics": metrics,
            "selections": [item.to_dict() for item in selections],
            "resolutions": [item.to_dict() for item in resolutions],
            "claims": {
                "external_problem_solution_claimed": False,
                "automated_external_submission_claimed": False,
                "copied_external_statement_claimed": False,
                "copied_community_solution_claimed": False,
                "hidden_test_extraction_claimed": False,
                "training_without_permission_claimed": False,
                "platform_affiliation_claimed": False,
                "general_algorithm_correctness_claimed": False,
                "neural_training_claimed": False,
                "no_permanent_total_cap_claimed": policy.permanent_total_cap is None,
            },
        }
        receipt["receipt_sha256"] = sha256_hex(receipt)
        return receipt


def fixture_references(per_platform: int = 64) -> tuple[ProblemRef, ...]:
    references = []
    for platform_index, platform in enumerate(PLATFORMS):
        for ordinal in range(per_platform):
            tags = _SKILLS[(ordinal + platform_index) % len(_SKILLS)]
            content_class = "event_metadata" if platform.platform_id == "advent_of_code" else "problem_id_reference" if platform.platform_id == "project_euler" else "exercise_definition" if platform.platform_id == "exercism" else "problem_metadata"
            references.append(ProblemRef(platform.platform_id, f"fixture-{ordinal:05d}", f"{platform.display_name} fixture {ordinal}", tags, ((ordinal * 7 + platform_index * 11) % 100) / 99.0, content_class, f"{platform.platform_id}:fixture-{ordinal:05d}", ordinal % 19 == 0, ordinal % 7 == 0, {"fixture": True}))
    return tuple(references)


def _fraction(*parts: str) -> float:
    return int(sha256_hex(parts)[:12], 16) / float(16**12 - 1)


def _size(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + sum(_size(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return 1 + sum(_size(item) for item in value)
    if isinstance(value, (str, bytes)):
        return max(1, len(value))
    return 1
