from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence
import uuid

from .governance import ObjectiveVector, pareto_front


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        separators=(",", ": "),
    ) + "\n"


@dataclass(frozen=True)
class CandidateProfile:
    """Finite, serializable candidate used by the adversarial OAKBench."""

    name: str
    throughput: float
    memory_bytes: int
    latency_ms: float
    quality: float
    recovery_rate: float
    complexity: float
    overshoot: float
    source_mutations: int = 0
    remote_mutations: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("candidate name cannot be empty")
        if self.throughput <= 0.0:
            raise ValueError("throughput must be positive")
        if self.memory_bytes <= 0:
            raise ValueError("memory_bytes must be positive")
        if self.latency_ms <= 0.0:
            raise ValueError("latency_ms must be positive")
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError("quality must be between 0 and 1")
        if not 0.0 <= self.recovery_rate <= 1.0:
            raise ValueError("recovery_rate must be between 0 and 1")
        if self.complexity < 0.0 or self.overshoot < 0.0:
            raise ValueError("complexity and overshoot cannot be negative")
        if self.source_mutations < 0 or self.remote_mutations < 0:
            raise ValueError("mutation counters cannot be negative")

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload.pop("name")
        return _sha256_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":"))
        )[:16]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fingerprint"] = self.fingerprint
        return payload


@dataclass(frozen=True)
class AdversarialScenario:
    name: str
    load_factor: float = 1.0
    memory_pressure: float = 1.0
    latency_factor: float = 1.0
    duplicate_rate: float = 0.0
    invalid_rate: float = 0.0
    checkpoint_corruption: bool = False
    api_failure_rate: float = 0.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("scenario name cannot be empty")
        if self.load_factor <= 0.0:
            raise ValueError("load_factor must be positive")
        if self.memory_pressure <= 0.0 or self.latency_factor <= 0.0:
            raise ValueError("pressure factors must be positive")
        for value, label in (
            (self.duplicate_rate, "duplicate_rate"),
            (self.invalid_rate, "invalid_rate"),
            (self.api_failure_rate, "api_failure_rate"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenarioEvidence:
    candidate: str
    scenario: str
    throughput: float
    memory_bytes: int
    latency_ms: float
    quality: float
    recovery_rate: float
    passed: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AggregateEvidence:
    profile: CandidateProfile
    scenarios: tuple[ScenarioEvidence, ...]
    hard_gates_passed: bool
    mean_throughput: float
    peak_memory_bytes: int
    maximum_latency_ms: float
    worst_quality: float
    worst_recovery_rate: float
    failures: tuple[str, ...]

    @property
    def objective_vector(self) -> ObjectiveVector:
        return ObjectiveVector(
            name=self.profile.name,
            maximize={
                "throughput": self.mean_throughput,
                "quality": self.worst_quality,
                "recovery": self.worst_recovery_rate,
            },
            minimize={
                "memory": float(self.peak_memory_bytes),
                "latency": self.maximum_latency_ms,
                "complexity": self.profile.complexity,
                "overshoot": self.profile.overshoot,
            },
            metadata={
                "fingerprint": self.profile.fingerprint,
                "hard_gates_passed": self.hard_gates_passed,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "scenarios": [item.to_dict() for item in self.scenarios],
            "hard_gates_passed": self.hard_gates_passed,
            "mean_throughput": self.mean_throughput,
            "peak_memory_bytes": self.peak_memory_bytes,
            "maximum_latency_ms": self.maximum_latency_ms,
            "worst_quality": self.worst_quality,
            "worst_recovery_rate": self.worst_recovery_rate,
            "failures": list(self.failures),
            "objective_vector": self.objective_vector.to_dict(),
        }


class AdversarialOAKBench:
    """Deterministic finite stress evaluator for policy candidates."""

    def __init__(
        self,
        *,
        quality_floor: float = 0.95,
        recovery_floor: float = 0.90,
    ):
        if not 0.0 <= quality_floor <= 1.0:
            raise ValueError("quality_floor must be between 0 and 1")
        if not 0.0 <= recovery_floor <= 1.0:
            raise ValueError("recovery_floor must be between 0 and 1")
        self.quality_floor = quality_floor
        self.recovery_floor = recovery_floor

    def evaluate_scenario(
        self,
        profile: CandidateProfile,
        scenario: AdversarialScenario,
    ) -> ScenarioEvidence:
        useful_fraction = max(
            0.01,
            1.0 - scenario.invalid_rate - 0.5 * scenario.duplicate_rate,
        )
        throughput = (
            profile.throughput
            * scenario.load_factor
            * useful_fraction
            / scenario.latency_factor
        )
        memory_bytes = int(
            round(
                profile.memory_bytes
                * scenario.memory_pressure
                * (1.0 + scenario.duplicate_rate)
            )
        )
        latency_ms = (
            profile.latency_ms
            * scenario.latency_factor
            * (1.0 + 2.0 * scenario.api_failure_rate)
        )
        quality = max(
            0.0,
            profile.quality
            - 0.40 * scenario.invalid_rate
            - 0.10 * scenario.duplicate_rate,
        )
        recovery_rate = max(
            0.0,
            profile.recovery_rate
            - (0.45 if scenario.checkpoint_corruption else 0.0)
            - 0.25 * scenario.api_failure_rate,
        )

        failures: list[str] = []
        if quality < self.quality_floor:
            failures.append("quality_floor")
        if recovery_rate < self.recovery_floor:
            failures.append("recovery_floor")
        if profile.source_mutations:
            failures.append("source_mutation")
        if profile.remote_mutations:
            failures.append("remote_mutation")

        return ScenarioEvidence(
            candidate=profile.name,
            scenario=scenario.name,
            throughput=throughput,
            memory_bytes=memory_bytes,
            latency_ms=latency_ms,
            quality=quality,
            recovery_rate=recovery_rate,
            passed=not failures,
            failures=tuple(failures),
        )

    def evaluate(
        self,
        profile: CandidateProfile,
        scenarios: Sequence[AdversarialScenario],
    ) -> AggregateEvidence:
        if not scenarios:
            raise ValueError("at least one adversarial scenario is required")
        evidence = tuple(self.evaluate_scenario(profile, item) for item in scenarios)
        failures = tuple(
            f"{item.scenario}:{failure}"
            for item in evidence
            for failure in item.failures
        )
        return AggregateEvidence(
            profile=profile,
            scenarios=evidence,
            hard_gates_passed=not failures,
            mean_throughput=mean(item.throughput for item in evidence),
            peak_memory_bytes=max(item.memory_bytes for item in evidence),
            maximum_latency_ms=max(item.latency_ms for item in evidence),
            worst_quality=min(item.quality for item in evidence),
            worst_recovery_rate=min(item.recovery_rate for item in evidence),
            failures=failures,
        )


@dataclass(frozen=True)
class CanaryPolicy:
    stages: tuple[float, ...] = (0.01, 0.05, 0.20, 0.50, 1.00)
    maximum_quality_drop: float = 0.01
    maximum_latency_ratio: float = 1.20
    maximum_memory_ratio: float = 1.25
    minimum_recovery_rate: float = 0.95

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("at least one canary stage is required")
        if tuple(sorted(self.stages)) != self.stages:
            raise ValueError("canary stages must be sorted")
        if self.stages[-1] != 1.0:
            raise ValueError("the final canary stage must be 1.0")
        if any(stage <= 0.0 or stage > 1.0 for stage in self.stages):
            raise ValueError("canary stages must be in (0, 1]")
        if self.maximum_quality_drop < 0.0:
            raise ValueError("maximum_quality_drop cannot be negative")
        if self.maximum_latency_ratio < 1.0 or self.maximum_memory_ratio < 1.0:
            raise ValueError("resource ratios must be at least 1")
        if not 0.0 <= self.minimum_recovery_rate <= 1.0:
            raise ValueError("minimum_recovery_rate must be between 0 and 1")


@dataclass(frozen=True)
class CanarySample:
    stage: float
    quality: float
    latency_ms: float
    memory_bytes: int
    recovery_rate: float

    def __post_init__(self) -> None:
        if not 0.0 < self.stage <= 1.0:
            raise ValueError("stage must be in (0, 1]")
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError("quality must be between 0 and 1")
        if self.latency_ms <= 0.0 or self.memory_bytes <= 0:
            raise ValueError("latency and memory must be positive")
        if not 0.0 <= self.recovery_rate <= 1.0:
            raise ValueError("recovery_rate must be between 0 and 1")


@dataclass(frozen=True)
class CanaryDecision:
    stage: float
    action: str
    reasons: tuple[str, ...]
    rollback_required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanaryReport:
    status: str
    decisions: tuple[CanaryDecision, ...]
    rollback_plan: Mapping[str, Any]
    automatic_promotion: bool = False
    automatic_merge: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "decisions": [item.to_dict() for item in self.decisions],
            "rollback_plan": dict(self.rollback_plan),
            "automatic_promotion": self.automatic_promotion,
            "automatic_merge": self.automatic_merge,
        }


class CanaryPromotionEngine:
    """Offline canary judge. It emits decisions but performs no deployment."""

    def __init__(self, policy: CanaryPolicy | None = None):
        self.policy = policy or CanaryPolicy()

    def run(
        self,
        *,
        baseline: AggregateEvidence,
        samples: Sequence[CanarySample],
        rollback_target: str,
    ) -> CanaryReport:
        expected = self.policy.stages
        actual = tuple(item.stage for item in samples)
        if actual != expected:
            raise ValueError("canary samples must exactly match the configured stages")

        decisions: list[CanaryDecision] = []
        for sample in samples:
            reasons: list[str] = []
            if sample.quality < baseline.worst_quality - self.policy.maximum_quality_drop:
                reasons.append("quality_regression")
            if sample.latency_ms > baseline.maximum_latency_ms * self.policy.maximum_latency_ratio:
                reasons.append("latency_regression")
            if sample.memory_bytes > baseline.peak_memory_bytes * self.policy.maximum_memory_ratio:
                reasons.append("memory_regression")
            if sample.recovery_rate < self.policy.minimum_recovery_rate:
                reasons.append("recovery_regression")

            if reasons:
                decisions.append(
                    CanaryDecision(
                        stage=sample.stage,
                        action="ROLLBACK",
                        reasons=tuple(reasons),
                        rollback_required=True,
                    )
                )
                return CanaryReport(
                    status="rolled_back",
                    decisions=tuple(decisions),
                    rollback_plan={
                        "target": rollback_target,
                        "trigger_stage": sample.stage,
                        "automatic_execution": False,
                        "requires_human_approval": True,
                    },
                )

            action = "PROMOTION_CANDIDATE" if sample.stage == 1.0 else "ADVANCE"
            decisions.append(
                CanaryDecision(
                    stage=sample.stage,
                    action=action,
                    reasons=("all canary gates passed",),
                    rollback_required=False,
                )
            )

        return CanaryReport(
            status="promotion_candidate",
            decisions=tuple(decisions),
            rollback_plan={
                "target": rollback_target,
                "trigger_stage": None,
                "automatic_execution": False,
                "requires_human_approval": True,
            },
        )


class ProofBundleWriter:
    """Writes a content-addressed, transportable evidence bundle."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def write(
        self,
        *,
        aggregate: AggregateEvidence,
        scenarios: Sequence[AdversarialScenario],
        canary: CanaryReport,
        authority: Mapping[str, Any],
    ) -> dict[str, Any]:
        bundle = self.root / aggregate.profile.fingerprint
        bundle.mkdir(parents=True, exist_ok=True)
        payloads = {
            "candidate.json": aggregate.profile.to_dict(),
            "adversarial-scenarios.json": [item.to_dict() for item in scenarios],
            "oakbench-result.json": aggregate.to_dict(),
            "canary-report.json": canary.to_dict(),
            "rollback-plan.json": dict(canary.rollback_plan),
            "authority.json": dict(authority),
        }

        hashes: dict[str, str] = {}
        for name, payload in payloads.items():
            text = _canonical_json(payload)
            (bundle / name).write_text(text, encoding="utf-8")
            hashes[name] = _sha256_text(text)

        manifest_core = {
            "candidate": aggregate.profile.name,
            "fingerprint": aggregate.profile.fingerprint,
            "files": hashes,
            "hard_gates_passed": aggregate.hard_gates_passed,
            "canary_status": canary.status,
            "source_mutations": int(authority.get("source_mutations", 0)),
            "remote_mutations": int(authority.get("remote_mutations", 0)),
        }
        bundle_id = _sha256_text(
            json.dumps(manifest_core, sort_keys=True, separators=(",", ":"))
        )
        manifest = {
            **manifest_core,
            "bundle_id": bundle_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        (bundle / "manifest.json").write_text(
            _canonical_json(manifest),
            encoding="utf-8",
        )
        return {
            "path": str(bundle),
            **manifest,
        }


def default_adversarial_scenarios() -> tuple[AdversarialScenario, ...]:
    return (
        AdversarialScenario("nominal"),
        AdversarialScenario(
            "duplicate-storm",
            load_factor=1.15,
            memory_pressure=1.10,
            duplicate_rate=0.20,
        ),
        AdversarialScenario(
            "invalid-input",
            invalid_rate=0.08,
        ),
        AdversarialScenario(
            "checkpoint-corruption",
            checkpoint_corruption=True,
        ),
        AdversarialScenario(
            "api-latency",
            latency_factor=1.80,
            api_failure_rate=0.08,
        ),
    )


def _samples_from_aggregate(
    aggregate: AggregateEvidence,
    *,
    quality_penalty_at_stage: Mapping[float, float] | None = None,
) -> tuple[CanarySample, ...]:
    penalties = dict(quality_penalty_at_stage or {})
    return tuple(
        CanarySample(
            stage=stage,
            quality=max(0.0, aggregate.profile.quality - penalties.get(stage, 0.0)),
            latency_ms=aggregate.profile.latency_ms,
            memory_bytes=aggregate.profile.memory_bytes,
            recovery_rate=aggregate.profile.recovery_rate,
        )
        for stage in CanaryPolicy().stages
    )


class RecursiveEvolutionLab:
    """R0.6 proof-carrying, adversarial and rollback-aware laboratory."""

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.authority = {
            "source_mutations": 0,
            "remote_mutations": 0,
            "automatic_pull_request": False,
            "automatic_merge": False,
            "automatic_promotion": False,
            "human_approval_required": True,
            "scalar_score_has_final_authority": False,
        }

    def run(self) -> dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        run_id = f"evolution-{uuid.uuid4().hex[:16]}"
        scenarios = default_adversarial_scenarios()
        bench = AdversarialOAKBench(quality_floor=0.94, recovery_floor=0.50)

        baseline_profile = CandidateProfile(
            "incumbent",
            throughput=100.0,
            memory_bytes=1_000_000,
            latency_ms=100.0,
            quality=0.99,
            recovery_rate=0.99,
            complexity=1.0,
            overshoot=0.20,
        )
        candidates = (
            CandidateProfile(
                "fast",
                throughput=135.0,
                memory_bytes=1_120_000,
                latency_ms=86.0,
                quality=0.99,
                recovery_rate=0.99,
                complexity=1.15,
                overshoot=0.30,
            ),
            CandidateProfile(
                "lean",
                throughput=108.0,
                memory_bytes=760_000,
                latency_ms=99.0,
                quality=0.99,
                recovery_rate=0.99,
                complexity=0.90,
                overshoot=0.12,
            ),
            CandidateProfile(
                "fragile",
                throughput=160.0,
                memory_bytes=900_000,
                latency_ms=75.0,
                quality=0.965,
                recovery_rate=0.60,
                complexity=1.30,
                overshoot=0.80,
            ),
            CandidateProfile(
                "dominated",
                throughput=90.0,
                memory_bytes=1_300_000,
                latency_ms=130.0,
                quality=0.98,
                recovery_rate=0.98,
                complexity=1.60,
                overshoot=0.60,
            ),
        )

        baseline = bench.evaluate(baseline_profile, scenarios)
        evaluated = tuple(bench.evaluate(item, scenarios) for item in candidates)
        eligible = tuple(item for item in evaluated if item.hard_gates_passed)
        front_vectors = pareto_front(item.objective_vector for item in eligible)
        front_names = tuple(item.name for item in front_vectors)
        rejected = tuple(
            item.profile.name for item in evaluated if not item.hard_gates_passed
        )
        dominated = tuple(
            item.profile.name
            for item in eligible
            if item.profile.name not in front_names
        )

        engine = CanaryPromotionEngine()
        safe = next(item for item in eligible if item.profile.name == "fast")
        safe_canary = engine.run(
            baseline=baseline,
            samples=_samples_from_aggregate(safe),
            rollback_target=baseline.profile.fingerprint,
        )
        risky_canary = engine.run(
            baseline=baseline,
            samples=_samples_from_aggregate(
                safe,
                quality_penalty_at_stage={0.20: 0.06, 0.50: 0.06, 1.00: 0.06},
            ),
            rollback_target=baseline.profile.fingerprint,
        )

        bundle_writer = ProofBundleWriter(self.output_dir / "proof-bundles")
        bundles = {
            item.profile.name: bundle_writer.write(
                aggregate=item,
                scenarios=scenarios,
                canary=(
                    safe_canary
                    if item.profile.name == "fast"
                    else CanaryReport(
                        status="not_run",
                        decisions=(),
                        rollback_plan={
                            "target": baseline.profile.fingerprint,
                            "automatic_execution": False,
                            "requires_human_approval": True,
                        },
                    )
                ),
                authority=self.authority,
            )
            for item in eligible
        }

        m_minus = self.output_dir / "m_minus.jsonl"
        with m_minus.open("w", encoding="utf-8") as handle:
            for item in evaluated:
                if item.hard_gates_passed:
                    continue
                handle.write(
                    json.dumps(
                        {
                            "event": "adversarial_candidate_rejected",
                            "candidate": item.profile.name,
                            "failures": list(item.failures),
                            "status": "negative_memory",
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )
            handle.write(
                json.dumps(
                    {
                        "event": "canary_regression_detected",
                        "candidate": "fast",
                        "status": risky_canary.status,
                        "decisions": [
                            item.to_dict() for item in risky_canary.decisions
                        ],
                        "rollback_plan": dict(risky_canary.rollback_plan),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

        m_plus = self.output_dir / "m_plus.jsonl"
        m_plus.write_text(
            json.dumps(
                {
                    "event": "proof_carrying_candidate_completed_canary",
                    "candidate": "fast",
                    "status": "promotion_candidate_requires_human_approval",
                    "proof_bundle": bundles["fast"]["bundle_id"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        report = {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "passed",
            "baseline": baseline.to_dict(),
            "candidates": [item.to_dict() for item in evaluated],
            "pareto_front": list(front_names),
            "dominated": list(dominated),
            "rejected": list(rejected),
            "safe_canary": safe_canary.to_dict(),
            "rollback_demonstration": risky_canary.to_dict(),
            "proof_bundles": bundles,
            "authority": self.authority,
            "next_gate": (
                "Human review and independent reproduction are required before any durable "
                "configuration change or deployment."
            ),
        }
        (self.output_dir / "evolution-report.json").write_text(
            _canonical_json(report),
            encoding="utf-8",
        )
        return report
