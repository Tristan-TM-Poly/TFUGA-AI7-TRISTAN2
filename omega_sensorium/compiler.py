from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

from omega_morphogenesis import MorphogenesisKernel

from .models import (
    Observable,
    ObservationCandidate,
    ObservationReceipt,
    ObservatoryGenome,
    ScienceQuestion,
    SensorCapability,
)


@dataclass(frozen=True)
class ReceiptGateResult:
    passed: bool
    reasons: tuple[str, ...]


class ScienceToSensorCompiler:
    """Compile a question into the least-cost existing sensor set that covers required observables.

    This bounded reference implementation searches existing capabilities first. Cardinality only
    breaks equal-cost ties; fewer devices are not automatically better than a cheaper combination.
    It does not claim to synthesize physically realizable hardware from first principles.
    """

    def compile(
        self,
        question: ScienceQuestion,
        observables: Sequence[Observable],
        sensors: Sequence[SensorCapability],
        *,
        permissions: Sequence[str] = (),
        provenance: Sequence[str] = (),
    ) -> ObservatoryGenome | None:
        required = tuple(observables)
        if not required:
            return ObservatoryGenome(
                genome_id=f"obs-{question.question_id}-no-action",
                question_id=question.question_id,
                hypothesis_ids=question.hypothesis_ids,
                observable_ids=(),
                sensor_ids=(),
                permissions=tuple(permissions),
                provenance=tuple(provenance),
            )

        feasible = [s for s in sensors if any(s.supports(o) for o in required)]
        best: tuple[SensorCapability, ...] | None = None
        best_key: tuple[float, int, tuple[str, ...]] | None = None
        for n in range(1, len(feasible) + 1):
            for subset in combinations(feasible, n):
                if all(any(sensor.supports(obs) for sensor in subset) for obs in required):
                    cost = sum(max(sensor.resource_cost, 0.0) for sensor in subset)
                    ids = tuple(sorted(sensor.sensor_id for sensor in subset))
                    key = (cost, n, ids)
                    if best_key is None or key < best_key:
                        best, best_key = subset, key

        if best is None:
            return None

        return ObservatoryGenome(
            genome_id=f"obs-{question.question_id}-v1",
            question_id=question.question_id,
            hypothesis_ids=question.hypothesis_ids,
            observable_ids=tuple(obs.observable_id for obs in required),
            sensor_ids=tuple(sorted(sensor.sensor_id for sensor in best)),
            permissions=tuple(permissions),
            provenance=tuple(provenance),
        )


class MinimalWitnessCompiler:
    """Select the cheapest observation that crosses explicit discrimination/calibration thresholds."""

    def select(
        self,
        candidates: Iterable[ObservationCandidate],
        *,
        min_discrimination: float,
        min_calibration: float = 0.0,
        baseline_value: float = 0.0,
    ) -> ObservationCandidate | None:
        valid = [
            c
            for c in candidates
            if c.discrimination_power >= min_discrimination
            and c.calibration_confidence >= min_calibration
            and c.value() > baseline_value
        ]
        if not valid:
            return None
        return min(valid, key=lambda c: (c.resource_cost, -c.value(), c.candidate_id))


class ActiveObservationEngine:
    """Rank observations by proof-oriented information value, while preserving NO_ACTION as baseline."""

    def rank(
        self,
        candidates: Iterable[ObservationCandidate],
        *,
        baseline_value: float = 0.0,
    ) -> list[ObservationCandidate]:
        return sorted(
            (c for c in candidates if c.value() > baseline_value),
            key=lambda c: (-c.value(), c.resource_cost, c.candidate_id),
        )

    def choose(
        self,
        candidates: Iterable[ObservationCandidate],
        *,
        baseline_value: float = 0.0,
    ) -> ObservationCandidate | None:
        ranked = self.rank(candidates, baseline_value=baseline_value)
        return ranked[0] if ranked else None


class ObservationCourt:
    """Non-compensatory receipt gates for observations used as scientific evidence."""

    def verify_receipt(self, receipt: ObservationReceipt) -> ReceiptGateResult:
        reasons: list[str] = []
        if receipt.generator_id == receipt.verifier_id:
            reasons.append("Generator != Judge violated")
        if not receipt.sensor_ids:
            reasons.append("at least one sensor is required")
        if not receipt.raw_data_hashes:
            reasons.append("raw data hashes are required")
        if not receipt.processing_pipeline:
            reasons.append("processing pipeline is required")
        if not receipt.provenance:
            reasons.append("provenance is required")
        if not 0.0 <= receipt.uncertainty <= 1.0:
            reasons.append("uncertainty must be in [0,1]")
        missing_cal = [s for s in receipt.sensor_ids if not receipt.calibration_versions.get(s)]
        if missing_cal:
            reasons.append("calibration version required for every sensor")
        return ReceiptGateResult(not reasons, tuple(reasons))


class MetaSensorium:
    """Facade that reuses the canonical morphogenesis kernel instead of duplicating meta-policy."""

    def __init__(self) -> None:
        self.morphogenesis = MorphogenesisKernel()
        self.science_to_sensor = ScienceToSensorCompiler()
        self.minimal_witness = MinimalWitnessCompiler()
        self.active_observation = ActiveObservationEngine()
        self.court = ObservationCourt()

    def should_create_new_meta_layer(
        self,
        *,
        verified_out_of_sample_gain: float,
        meta_complexity_cost: float,
        expressible_by_current_kernel: bool,
    ) -> bool:
        return self.morphogenesis.should_create_meta_level(
            verified_out_of_sample_gain,
            meta_complexity_cost,
            expressible_by_current_kernel,
        )
