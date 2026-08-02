from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence
import uuid

from .core import (
    AdaptiveController,
    CapacityPolicy,
    MMinusLedger,
    SyntheticCapacityExecutor,
)
from .streaming import MPlusLedger, RangeWorkSource


@dataclass(frozen=True)
class SelfImprovementScenario:
    """Finite OAKBench scenario used to compare controller variants."""

    name: str
    work_items: int
    initial_capacity: int
    initial_batch: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("scenario name cannot be empty")
        if self.work_items < 0:
            raise ValueError("work_items cannot be negative")
        if self.initial_capacity < 1:
            raise ValueError("initial_capacity must be positive")
        if self.initial_batch < 1:
            raise ValueError("initial_batch must be positive")


@dataclass(frozen=True)
class ControllerVariant:
    """Serializable controller/executor policy candidate.

    Candidate streams are consumed until exhaustion. The laboratory has no
    permanent candidate-count or round-count ceiling.
    """

    name: str
    stable_growth: float = 2.0
    cautious_growth: float = 1.25
    redesign_factor: float = 2.0
    pressure_soft: float = 0.75
    pressure_hard: float = 1.0
    quality_floor: float = 0.95

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("variant name cannot be empty")
        CapacityPolicy(
            quality_floor=self.quality_floor,
            pressure_soft=self.pressure_soft,
            pressure_hard=self.pressure_hard,
            stable_growth=self.stable_growth,
            cautious_growth=self.cautious_growth,
        )
        if self.redesign_factor <= 1.0:
            raise ValueError("redesign_factor must be greater than 1")

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(
            {
                "stable_growth": self.stable_growth,
                "cautious_growth": self.cautious_growth,
                "redesign_factor": self.redesign_factor,
                "pressure_soft": self.pressure_soft,
                "pressure_hard": self.pressure_hard,
                "quality_floor": self.quality_floor,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fingerprint"] = self.fingerprint
        return payload


@dataclass(frozen=True)
class ScenarioOutcome:
    scenario: str
    status: str
    total_integrated: int
    total_rejected: int
    total_duplicates: int
    iterations: int
    saturation_count: int
    redesign_count: int
    largest_safe_batch: int
    final_capacity: int
    negative_memory_events: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VariantOutcome:
    variant: ControllerVariant
    scenarios: tuple[ScenarioOutcome, ...]
    completed: bool
    total_integrated: int
    total_rejected: int
    total_duplicates: int
    total_iterations: int
    total_saturations: int
    total_redesigns: int
    largest_safe_batch: int
    efficiency_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant.to_dict(),
            "scenarios": [item.to_dict() for item in self.scenarios],
            "completed": self.completed,
            "total_integrated": self.total_integrated,
            "total_rejected": self.total_rejected,
            "total_duplicates": self.total_duplicates,
            "total_iterations": self.total_iterations,
            "total_saturations": self.total_saturations,
            "total_redesigns": self.total_redesigns,
            "largest_safe_batch": self.largest_safe_batch,
            "efficiency_score": self.efficiency_score,
        }


@dataclass(frozen=True)
class PromotionDecision:
    status: str
    incumbent: str
    selected: str | None
    selected_fingerprint: str | None
    improvement_ratio: float
    reasons: tuple[str, ...]
    requires_human_approval: bool = True
    remote_mutations: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SelfImprovementReport:
    run_id: str
    generated_at: str
    baseline: VariantOutcome
    candidates: tuple[VariantOutcome, ...]
    decision: PromotionDecision
    candidate_stream_exhausted: bool
    no_permanent_candidate_cap: bool = True
    no_source_mutation: bool = True
    no_auto_merge: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "baseline": self.baseline.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "decision": self.decision.to_dict(),
            "candidate_stream_exhausted": self.candidate_stream_exhausted,
            "no_permanent_candidate_cap": self.no_permanent_candidate_cap,
            "no_source_mutation": self.no_source_mutation,
            "no_auto_merge": self.no_auto_merge,
        }


def default_scenarios(work_items: int = 60_000) -> tuple[SelfImprovementScenario, ...]:
    """Build a multi-scale finite experiment without defining a global cap."""

    if work_items < 3:
        raise ValueError("work_items must be at least 3")
    small = max(1, work_items // 6)
    medium = max(1, work_items // 3)
    large = work_items - small - medium
    return (
        SelfImprovementScenario("small-frontier", small, 64, 32),
        SelfImprovementScenario("medium-frontier", medium, 128, 64),
        SelfImprovementScenario("large-frontier", large, 256, 128),
    )


def adaptive_candidate_stream(
    incumbent: ControllerVariant,
    baseline: VariantOutcome,
) -> Iterator[ControllerVariant]:
    """Generate a deterministic seed neighborhood from observed M-minus.

    The laboratory accepts any iterable and imposes no permanent candidate
    count. This built-in stream is only an offline starting neighborhood.
    """

    pressure_multiplier = 1.5 if baseline.total_saturations else 1.25
    yield ControllerVariant(
        name="mminus-capacity-redesign",
        stable_growth=incumbent.stable_growth,
        cautious_growth=incumbent.cautious_growth,
        redesign_factor=incumbent.redesign_factor * pressure_multiplier,
        pressure_soft=incumbent.pressure_soft,
        pressure_hard=incumbent.pressure_hard,
        quality_floor=incumbent.quality_floor,
    )
    yield ControllerVariant(
        name="mminus-capacity-redesign-plus",
        stable_growth=incumbent.stable_growth,
        cautious_growth=incumbent.cautious_growth,
        redesign_factor=incumbent.redesign_factor * 2.0,
        pressure_soft=incumbent.pressure_soft,
        pressure_hard=incumbent.pressure_hard,
        quality_floor=incumbent.quality_floor,
    )
    yield ControllerVariant(
        name="mminus-balanced-ramp",
        stable_growth=max(1.01, incumbent.stable_growth * 0.875),
        cautious_growth=max(1.01, incumbent.cautious_growth * 0.96),
        redesign_factor=incumbent.redesign_factor * pressure_multiplier,
        pressure_soft=min(0.95, incumbent.pressure_soft + 0.05),
        pressure_hard=incumbent.pressure_hard,
        quality_floor=incumbent.quality_floor,
    )


def iter_variants_jsonl(path: str | Path) -> Iterator[ControllerVariant]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(payload, dict):
                raise TypeError(f"{source}:{line_number}: candidate must be an object")
            try:
                yield ControllerVariant(
                    name=str(payload["name"]),
                    stable_growth=float(payload.get("stable_growth", 2.0)),
                    cautious_growth=float(payload.get("cautious_growth", 1.25)),
                    redesign_factor=float(payload.get("redesign_factor", 2.0)),
                    pressure_soft=float(payload.get("pressure_soft", 0.75)),
                    pressure_hard=float(payload.get("pressure_hard", 1.0)),
                    quality_floor=float(payload.get("quality_floor", 0.95)),
                )
            except KeyError as exc:
                raise ValueError(f"{source}:{line_number}: missing field {exc.args[0]}") from exc


class SelfImprovementLab:
    """Offline recursive policy laboratory for Omega-SANS-PLAFOND-T-infinity.

    It evaluates the current policy, derives or consumes improvement candidates,
    rejects regressions, records M-minus/M-plus, and emits a human-reviewable
    promotion plan. It never edits source files, pushes branches, opens PRs, or
    merges.
    """

    def __init__(
        self,
        output_dir: str | Path,
        *,
        scenarios: Sequence[SelfImprovementScenario] | None = None,
        incumbent: ControllerVariant | None = None,
        minimum_improvement_ratio: float = 0.02,
    ):
        if minimum_improvement_ratio < 0.0:
            raise ValueError("minimum_improvement_ratio cannot be negative")
        self.output_dir = Path(output_dir)
        self.scenarios = tuple(scenarios or default_scenarios())
        if not self.scenarios:
            raise ValueError("at least one scenario is required")
        self.incumbent = incumbent or ControllerVariant(name="incumbent-r0.3")
        self.minimum_improvement_ratio = minimum_improvement_ratio

    def run(
        self,
        candidates: Iterable[ControllerVariant] | None = None,
    ) -> SelfImprovementReport:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        run_id = f"self-improve-{uuid.uuid4().hex[:16]}"
        baseline = self._evaluate(self.incumbent, run_id=run_id, role="baseline")
        stream = candidates if candidates is not None else adaptive_candidate_stream(self.incumbent, baseline)

        seen = {self.incumbent.fingerprint}
        outcomes: list[VariantOutcome] = []
        for candidate in stream:
            if candidate.fingerprint in seen:
                self._append_jsonl(
                    self.output_dir / "self_improvement_m_minus.jsonl",
                    {
                        "event": "candidate_duplicate",
                        "candidate": candidate.to_dict(),
                        "status": "rejected_before_evaluation",
                    },
                )
                continue
            seen.add(candidate.fingerprint)
            outcome = self._evaluate(candidate, run_id=run_id, role="candidate")
            outcomes.append(outcome)
            self._append_jsonl(self.output_dir / "candidate-results.jsonl", outcome.to_dict())

        decision = self._decide(baseline, outcomes)
        self._record_decision_memory(baseline, outcomes, decision)

        report = SelfImprovementReport(
            run_id=run_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            baseline=baseline,
            candidates=tuple(outcomes),
            decision=decision,
            candidate_stream_exhausted=True,
        )
        self._write_json(self.output_dir / "self-improvement-report.json", report.to_dict())
        self._write_json(self.output_dir / "promotion-plan.json", self._promotion_plan(report))
        return report

    def _evaluate(
        self,
        variant: ControllerVariant,
        *,
        run_id: str,
        role: str,
    ) -> VariantOutcome:
        del run_id
        scenario_outcomes: list[ScenarioOutcome] = []
        variant_dir = self.output_dir / "variants" / f"{role}-{variant.fingerprint}"
        variant_dir.mkdir(parents=True, exist_ok=True)

        for scenario in self.scenarios:
            ledger_path = variant_dir / f"{scenario.name}.m_minus.jsonl"
            if ledger_path.exists():
                ledger_path.unlink()
            ledger = MMinusLedger(ledger_path)
            source = RangeWorkSource(scenario.work_items)
            executor = SyntheticCapacityExecutor(
                capacity=scenario.initial_capacity,
                redesign_factor=variant.redesign_factor,
                quality_score=0.99,
                allow_redesign=True,
            )
            controller = AdaptiveController(
                source,
                executor,
                initial_batch=scenario.initial_batch,
                policy=CapacityPolicy(
                    quality_floor=variant.quality_floor,
                    pressure_soft=variant.pressure_soft,
                    pressure_hard=variant.pressure_hard,
                    stable_growth=variant.stable_growth,
                    cautious_growth=variant.cautious_growth,
                ),
                ledger=ledger,
                checkpoint_path=variant_dir / f"{scenario.name}.checkpoint.json",
            )
            result = controller.run()
            scenario_outcomes.append(
                ScenarioOutcome(
                    scenario=scenario.name,
                    status=result.status,
                    total_integrated=result.total_integrated,
                    total_rejected=result.total_rejected,
                    total_duplicates=result.total_duplicates,
                    iterations=result.iterations,
                    saturation_count=result.saturation_count,
                    redesign_count=result.redesign_count,
                    largest_safe_batch=result.largest_safe_batch,
                    final_capacity=executor.capacity,
                    negative_memory_events=len(ledger.events),
                )
            )

        completed = all(item.status == "completed" for item in scenario_outcomes)
        total_integrated = sum(item.total_integrated for item in scenario_outcomes)
        total_rejected = sum(item.total_rejected for item in scenario_outcomes)
        total_duplicates = sum(item.total_duplicates for item in scenario_outcomes)
        total_iterations = sum(item.iterations for item in scenario_outcomes)
        total_saturations = sum(item.saturation_count for item in scenario_outcomes)
        total_redesigns = sum(item.redesign_count for item in scenario_outcomes)
        largest_safe_batch = max((item.largest_safe_batch for item in scenario_outcomes), default=0)
        denominator = max(1, total_iterations + 8 * total_saturations + 4 * total_redesigns)
        efficiency_score = total_integrated / denominator

        return VariantOutcome(
            variant=variant,
            scenarios=tuple(scenario_outcomes),
            completed=completed,
            total_integrated=total_integrated,
            total_rejected=total_rejected,
            total_duplicates=total_duplicates,
            total_iterations=total_iterations,
            total_saturations=total_saturations,
            total_redesigns=total_redesigns,
            largest_safe_batch=largest_safe_batch,
            efficiency_score=efficiency_score,
        )

    def _decide(
        self,
        baseline: VariantOutcome,
        candidates: Sequence[VariantOutcome],
    ) -> PromotionDecision:
        eligible: list[VariantOutcome] = []
        rejection_reasons: list[str] = []

        for outcome in candidates:
            reasons = self._regressions(baseline, outcome)
            if reasons:
                rejection_reasons.append(f"{outcome.variant.name}: " + "; ".join(reasons))
                continue
            ratio = self._ratio(baseline.efficiency_score, outcome.efficiency_score)
            if ratio < self.minimum_improvement_ratio:
                rejection_reasons.append(
                    f"{outcome.variant.name}: efficiency gain {ratio:.6f} below required "
                    f"{self.minimum_improvement_ratio:.6f}"
                )
                continue
            eligible.append(outcome)

        if not eligible:
            return PromotionDecision(
                status="no_promotion",
                incumbent=baseline.variant.name,
                selected=None,
                selected_fingerprint=None,
                improvement_ratio=0.0,
                reasons=tuple(rejection_reasons or ("candidate stream contained no eligible improvement",)),
            )

        selected = max(
            eligible,
            key=lambda item: (
                item.efficiency_score,
                -item.total_saturations,
                -item.total_iterations,
                item.largest_safe_batch,
            ),
        )
        ratio = self._ratio(baseline.efficiency_score, selected.efficiency_score)
        return PromotionDecision(
            status="promotion_proposed",
            incumbent=baseline.variant.name,
            selected=selected.variant.name,
            selected_fingerprint=selected.variant.fingerprint,
            improvement_ratio=ratio,
            reasons=(
                "all scenarios completed",
                "no integrated-work, rejection, duplication, iteration, or saturation regression",
                f"efficiency improved by {ratio:.6f}",
                "promotion remains configuration-only and requires human approval",
            ),
        )

    @staticmethod
    def _regressions(
        baseline: VariantOutcome,
        candidate: VariantOutcome,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if not candidate.completed:
            reasons.append("not all scenarios completed")
        if candidate.total_integrated < baseline.total_integrated:
            reasons.append("integrated work regressed")
        if candidate.total_rejected > baseline.total_rejected:
            reasons.append("rejections increased")
        if candidate.total_duplicates > baseline.total_duplicates:
            reasons.append("duplicates increased")
        if candidate.total_iterations > baseline.total_iterations:
            reasons.append("iterations increased")
        if candidate.total_saturations > baseline.total_saturations:
            reasons.append("saturations increased")
        return tuple(reasons)

    @staticmethod
    def _ratio(previous: float, current: float) -> float:
        if previous <= 0.0:
            return float("inf") if current > 0.0 else 0.0
        return current / previous - 1.0

    def _record_decision_memory(
        self,
        baseline: VariantOutcome,
        candidates: Sequence[VariantOutcome],
        decision: PromotionDecision,
    ) -> None:
        selected = next(
            (item for item in candidates if item.variant.fingerprint == decision.selected_fingerprint),
            None,
        )
        for outcome in candidates:
            if selected is not None and outcome.variant.fingerprint == selected.variant.fingerprint:
                continue
            self._append_jsonl(
                self.output_dir / "self_improvement_m_minus.jsonl",
                {
                    "event_id": f"SIM-{uuid.uuid4().hex[:16]}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "candidate_not_promoted",
                    "candidate": outcome.variant.to_dict(),
                    "outcome": outcome.to_dict(),
                    "regressions": self._regressions(baseline, outcome),
                    "status": "negative_memory",
                },
            )

        if selected is None:
            return

        previous_frontier = max(1, int(round(baseline.efficiency_score * 1_000_000)))
        new_frontier = max(previous_frontier + 1, int(round(selected.efficiency_score * 1_000_000)))
        MPlusLedger(self.output_dir / "m_plus.jsonl").record(
            previous_frontier=previous_frontier,
            new_frontier=new_frontier,
            intervention=(
                "self_benchmark",
                f"controller_variant:{selected.variant.fingerprint}",
                f"redesign_factor:{selected.variant.redesign_factor}",
                f"stable_growth:{selected.variant.stable_growth}",
                f"cautious_growth:{selected.variant.cautious_growth}",
            ),
            repetitions=len(self.scenarios),
            quality_before=baseline.variant.quality_floor,
            quality_after=selected.variant.quality_floor,
            status="promotion_candidate_requires_human_approval",
        )

    def _promotion_plan(self, report: SelfImprovementReport) -> dict[str, Any]:
        selected = next(
            (
                item
                for item in report.candidates
                if item.variant.fingerprint == report.decision.selected_fingerprint
            ),
            None,
        )
        return {
            "run_id": report.run_id,
            "status": report.decision.status,
            "incumbent": report.baseline.variant.to_dict(),
            "selected": selected.variant.to_dict() if selected is not None else None,
            "evidence": {
                "baseline": report.baseline.to_dict(),
                "selected": selected.to_dict() if selected is not None else None,
                "improvement_ratio": report.decision.improvement_ratio,
            },
            "apply": {
                "automatic": False,
                "requires_human_approval": True,
                "source_mutations": 0,
                "remote_mutations": 0,
                "merge": False,
            },
            "next_gate": (
                "Review the candidate, reproduce on independent workloads, then update the "
                "machine-readable policy in a separate explicitly authorized change."
            ),
        }

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)
