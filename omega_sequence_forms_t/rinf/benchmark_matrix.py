"""Multi-scale benchmark matrix and campaign scheduler for R∞ MAX.

The matrix describes an unbounded family of deterministic benchmark cells.  A
finite run is selected by resources, value and risk; no permanent maximum case
count is embedded in the architecture.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import heapq
import json
from math import log2
from typing import Callable, Iterable, Iterator, Mapping, Sequence


class DifficultyAxis(str, Enum):
    TERM_COUNT = "term_count"
    PARAMETER_HEIGHT = "parameter_height"
    MODEL_ORDER = "model_order"
    MODEL_DEGREE = "model_degree"
    NOISE_LEVEL = "noise_level"
    MISSING_RATE = "missing_rate"
    OUTLIER_RATE = "outlier_rate"
    CONDITION_NUMBER = "condition_number"
    COMPETING_MODELS = "competing_models"
    REMOTE_DISTANCE = "remote_distance"
    DIMENSION = "dimension"
    PRECISION_BITS = "precision_bits"


FAMILY_IDS: tuple[str, ...] = (
    "polynomial",
    "quasi_polynomial",
    "rational_index",
    "constant_recurrence",
    "p_recursive",
    "hypergeometric",
    "q_hypergeometric",
    "rational_prony",
    "algebraic_generating_function",
    "d_finite",
    "automatic",
    "k_regular",
    "morphic",
    "multiplicative",
    "dirichlet_convolution",
    "moment_sequence",
    "continued_fraction",
    "orthogonal_polynomial",
    "nonlinear_recurrence",
    "koopman_lift",
    "asymptotic",
    "transseries",
    "stochastic",
    "multivariate",
    "algorithmic",
    "mixture",
    "piecewise",
    "sparse_event",
    "modular",
    "complex_oscillatory",
    "matrix_sequence",
    "tensor_sequence",
)


MUTATION_IDS: tuple[str, ...] = (
    "none",
    "single_tail_error",
    "single_random_error",
    "bounded_noise",
    "heteroscedastic_noise",
    "missing_block",
    "random_missing",
    "decimation",
    "index_shift",
    "value_scale",
    "value_offset",
    "precision_truncation",
    "modular_projection",
    "regime_switch",
    "competing_continuation",
    "branch_change",
    "singular_index",
    "parameter_drift",
    "subsequence_alias",
    "period_alias",
    "zero_insertion",
    "sign_flip",
    "segment_reversal",
    "convolution_mask",
    "arithmetic_reindex",
    "remote_only_failure",
    "basis_rotation",
    "rank_defect",
    "near_collision",
    "overflow_boundary",
    "underflow_boundary",
    "adversarial_formula",
)


VALIDATION_IDS: tuple[str, ...] = (
    "observed_fit",
    "heldout_contiguous",
    "heldout_remote",
    "subsequence",
    "random_mask",
    "mutation_suite",
    "roundtrip",
    "exact_substitution",
    "interval_enclosure",
    "cross_precision",
    "cross_language",
    "modular_reconstruction",
    "symbolic_identity",
    "counterexample_search",
    "independent_generator",
    "formal_skeleton",
)


@dataclass(frozen=True)
class BenchmarkCoordinate:
    family_index: int
    mutation_index: int
    validation_index: int
    scale_shell: int
    seed: int

    def __post_init__(self) -> None:
        if not 0 <= self.family_index < len(FAMILY_IDS):
            raise ValueError("family index outside benchmark atlas")
        if not 0 <= self.mutation_index < len(MUTATION_IDS):
            raise ValueError("mutation index outside benchmark atlas")
        if not 0 <= self.validation_index < len(VALIDATION_IDS):
            raise ValueError("validation index outside benchmark atlas")
        if self.scale_shell < 0:
            raise ValueError("scale shell must be non-negative")

    @property
    def family_id(self) -> str:
        return FAMILY_IDS[self.family_index]

    @property
    def mutation_id(self) -> str:
        return MUTATION_IDS[self.mutation_index]

    @property
    def validation_id(self) -> str:
        return VALIDATION_IDS[self.validation_index]

    def render(self) -> str:
        return (
            f"family={self.family_id};mutation={self.mutation_id};"
            f"validation={self.validation_id};shell={self.scale_shell};seed={self.seed}"
        )

    def digest(self) -> str:
        return sha256(self.render().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BenchmarkPlan:
    coordinate: BenchmarkCoordinate
    term_count: int
    holdout_count: int
    remote_indices: tuple[int, ...]
    precision_bits: int
    parameter_height: int
    expected_compute_units: float
    expected_storage_bytes: int
    expected_information_gain: float
    risk_score: float
    required_capabilities: tuple[str, ...]
    success_metrics: tuple[str, ...]

    @property
    def value_cost_ratio(self) -> float:
        return self.expected_information_gain / self.expected_compute_units if self.expected_compute_units else float("inf")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["coordinate"] = self.coordinate.render()
        payload["coordinate_digest"] = self.coordinate.digest()
        payload["value_cost_ratio"] = self.value_cost_ratio
        return payload


@dataclass(frozen=True)
class BenchmarkOutcome:
    coordinate_digest: str
    passed: bool
    metrics: Mapping[str, float | int | str | bool]
    failure_codes: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    counterexample_ids: tuple[str, ...]
    compute_spent: float
    storage_bytes: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class BenchmarkCampaign:
    campaign_id: str
    plans: list[BenchmarkPlan] = field(default_factory=list)
    outcomes: dict[str, BenchmarkOutcome] = field(default_factory=dict)
    stop_reason: str = "not_started"

    def add_plan(self, plan: BenchmarkPlan) -> None:
        digest = plan.coordinate.digest()
        if any(item.coordinate.digest() == digest for item in self.plans):
            raise ValueError("duplicate benchmark coordinate")
        self.plans.append(plan)

    def add_outcome(self, outcome: BenchmarkOutcome) -> None:
        if outcome.coordinate_digest not in {plan.coordinate.digest() for plan in self.plans}:
            raise KeyError("outcome does not match a planned coordinate")
        if outcome.coordinate_digest in self.outcomes:
            raise ValueError("duplicate benchmark outcome")
        self.outcomes[outcome.coordinate_digest] = outcome

    def receipt(self) -> dict[str, object]:
        outcomes = tuple(self.outcomes.values())
        payload = {
            "schema": "omega-benchmark-campaign/1",
            "campaign_id": self.campaign_id,
            "planned_cases": len(self.plans),
            "executed_cases": len(outcomes),
            "passed_cases": sum(outcome.passed for outcome in outcomes),
            "failed_cases": sum(not outcome.passed for outcome in outcomes),
            "counterexamples": sum(len(outcome.counterexample_ids) for outcome in outcomes),
            "compute_spent": sum(outcome.compute_spent for outcome in outcomes),
            "storage_bytes": sum(outcome.storage_bytes for outcome in outcomes),
            "families_covered": sorted({plan.coordinate.family_id for plan in self.plans}),
            "mutations_covered": sorted({plan.coordinate.mutation_id for plan in self.plans}),
            "validations_covered": sorted({plan.coordinate.validation_id for plan in self.plans}),
            "stop_reason": self.stop_reason,
            "permanent_total_cap": None,
            "global_identity_proved": False,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["receipt_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def shell_parameters(shell: int) -> dict[str, int | float]:
    if shell < 0:
        raise ValueError("shell must be non-negative")
    tier = shell // 16
    within = shell % 16
    term_count = 16 * (2 ** min(tier, 20)) + within * max(1, 2 ** max(0, tier - 2))
    holdout = max(2, term_count // (5 + within % 5))
    precision = 64 + 32 * min(tier, 30)
    parameter_height = 4 * (2 ** min(tier, 24)) + within
    remote_scale = 2 ** min(tier + 4, 40)
    noise_level = 0.0 if within < 4 else 10.0 ** (-(within - 2))
    return {
        "term_count": term_count,
        "holdout_count": holdout,
        "precision_bits": precision,
        "parameter_height": parameter_height,
        "remote_scale": remote_scale,
        "noise_level": noise_level,
    }


def plan_coordinate(coordinate: BenchmarkCoordinate) -> BenchmarkPlan:
    parameters = shell_parameters(coordinate.scale_shell)
    term_count = int(parameters["term_count"])
    holdout = int(parameters["holdout_count"])
    remote_scale = int(parameters["remote_scale"])
    remote = tuple(
        sorted(
            {
                term_count,
                term_count + 1,
                term_count * 2,
                term_count * 4,
                remote_scale,
                remote_scale + 1,
            }
        )
    )
    family_factor = 1.0 + coordinate.family_index / len(FAMILY_IDS)
    mutation_factor = 1.0 + coordinate.mutation_index / 8
    validation_factor = 1.0 + coordinate.validation_index / 16
    compute = max(0.1, family_factor * mutation_factor * validation_factor * log2(term_count + 2))
    storage = int(512 + term_count * (16 + int(parameters["precision_bits"]) // 8))
    information = (
        1.0
        + log2(term_count + 1)
        + coordinate.mutation_index / 4
        + coordinate.validation_index / 8
    )
    risk = min(1.0, coordinate.mutation_index / max(1, len(MUTATION_IDS) - 1))
    capabilities = ["exact_rational_core", "deterministic_receipts"]
    if coordinate.family_id in {"p_recursive", "d_finite"}:
        capabilities.append("operator_guessing")
    if coordinate.family_id in {"automatic", "k_regular", "morphic"}:
        capabilities.append("finite_kernel")
    if coordinate.mutation_id != "none":
        capabilities.append("adversarial_validation")
    if coordinate.validation_id == "cross_language":
        capabilities.extend(["rust_backend", "cpp_backend"])
    return BenchmarkPlan(
        coordinate=coordinate,
        term_count=term_count,
        holdout_count=holdout,
        remote_indices=remote,
        precision_bits=int(parameters["precision_bits"]),
        parameter_height=int(parameters["parameter_height"]),
        expected_compute_units=compute,
        expected_storage_bytes=storage,
        expected_information_gain=information,
        risk_score=risk,
        required_capabilities=tuple(capabilities),
        success_metrics=(
            "family_classification",
            "heldout_accuracy",
            "false_discovery_rate",
            "minimal_complexity_recovery",
            "counterexample_discovery",
            "calibration_error",
            "runtime",
            "memory",
        ),
    )


def coordinate_stream(*, seed: int = 0) -> Iterator[BenchmarkCoordinate]:
    shell = 0
    while True:
        for family in range(len(FAMILY_IDS)):
            for mutation in range(len(MUTATION_IDS)):
                validation = (family * 17 + mutation * 13 + shell * 7 + seed) % len(VALIDATION_IDS)
                yield BenchmarkCoordinate(family, mutation, validation, shell, seed)
        shell += 1


def plan_stream(*, seed: int = 0) -> Iterator[BenchmarkPlan]:
    for coordinate in coordinate_stream(seed=seed):
        yield plan_coordinate(coordinate)


def select_campaign(
    *,
    campaign_id: str,
    seed: int = 0,
    compute_budget: float,
    storage_budget_bytes: int,
    maximum_materialized_cases: int | None = None,
    minimum_value_cost_ratio: float = 0.0,
    scouting_window: int = 100_000,
) -> BenchmarkCampaign:
    if compute_budget <= 0 or storage_budget_bytes <= 0 or scouting_window <= 0:
        raise ValueError("campaign resources must be positive")
    if maximum_materialized_cases is not None and maximum_materialized_cases <= 0:
        raise ValueError("case limit must be positive")
    heap = []
    for ordinal, plan in enumerate(plan_stream(seed=seed)):
        if ordinal >= scouting_window:
            break
        priority = -(
            plan.value_cost_ratio
            + plan.expected_information_gain / max(plan.expected_storage_bytes, 1)
            - plan.risk_score * 0.1
        )
        heapq.heappush(heap, (priority, ordinal, plan))
    campaign = BenchmarkCampaign(campaign_id)
    compute_spent = 0.0
    storage_spent = 0
    while heap:
        if maximum_materialized_cases is not None and len(campaign.plans) >= maximum_materialized_cases:
            campaign.stop_reason = "campaign_case_cap"
            break
        _, _, plan = heapq.heappop(heap)
        if plan.value_cost_ratio < minimum_value_cost_ratio:
            campaign.stop_reason = "value_cost_threshold"
            break
        if compute_spent + plan.expected_compute_units > compute_budget:
            continue
        if storage_spent + plan.expected_storage_bytes > storage_budget_bytes:
            continue
        campaign.add_plan(plan)
        compute_spent += plan.expected_compute_units
        storage_spent += plan.expected_storage_bytes
    else:
        campaign.stop_reason = "scouting_frontier_exhausted"
    if not campaign.plans and campaign.stop_reason == "not_started":
        campaign.stop_reason = "no_plan_fits_resources"
    return campaign


def benchmark_atlas_receipt() -> dict[str, object]:
    payload = {
        "schema": "omega-benchmark-matrix-atlas/1",
        "families": list(FAMILY_IDS),
        "mutations": list(MUTATION_IDS),
        "validations": list(VALIDATION_IDS),
        "difficulty_axes": [axis.value for axis in DifficultyAxis],
        "base_cells_per_shell": len(FAMILY_IDS) * len(MUTATION_IDS),
        "shell_count": None,
        "permanent_total_cap": None,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["atlas_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload
