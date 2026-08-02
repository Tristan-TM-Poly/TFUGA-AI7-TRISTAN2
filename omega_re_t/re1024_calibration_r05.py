"""Software-only probabilistic calibration reports for RE-style frontiers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Iterable, Sequence


@dataclass(frozen=True)
class CalibrationCase:
    case_id: str
    probability: float
    observed: bool
    family: str = "synthetic"

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id cannot be blank")
        if not math.isfinite(self.probability) or not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be in [0, 1]")


@dataclass(frozen=True)
class CalibrationBin:
    lower: float
    upper: float
    count: int
    mean_probability: float
    observed_rate: float
    absolute_gap: float


@dataclass(frozen=True)
class CalibrationReport:
    logical_cases: int
    materialized_cases: int
    executed_cases: int
    software_tested_cases: int
    scientifically_verified_cases: int
    brier_score: float
    log_loss: float
    expected_calibration_error: float
    maximum_calibration_error: float
    accuracy_at_half: float
    bins: tuple[CalibrationBin, ...]
    digest: str
    claim: str = "software_calibration_only"


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def calibrate(
    cases: Iterable[CalibrationCase],
    *,
    bin_count: int = 10,
    logical_cases: int | None = None,
    materialized_cases: int | None = None,
) -> CalibrationReport:
    items = tuple(cases)
    if not items:
        raise ValueError("cases cannot be empty")
    if bin_count <= 0:
        raise ValueError("bin_count must be positive")
    logical = len(items) if logical_cases is None else logical_cases
    materialized = len(items) if materialized_cases is None else materialized_cases
    if logical < len(items) or materialized < len(items):
        raise ValueError("declared counts cannot be below executed count")
    epsilon = 1.0e-15
    brier = sum((case.probability - float(case.observed)) ** 2 for case in items) / len(items)
    log_loss = -sum(
        math.log(max(epsilon, case.probability if case.observed else 1.0 - case.probability))
        for case in items
    ) / len(items)
    bins: list[CalibrationBin] = []
    weighted_gap = 0.0
    max_gap = 0.0
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        selected = [
            case for case in items
            if lower <= case.probability < upper or (index == bin_count - 1 and case.probability == 1.0)
        ]
        if not selected:
            continue
        mean_probability = sum(case.probability for case in selected) / len(selected)
        observed_rate = sum(case.observed for case in selected) / len(selected)
        gap = abs(mean_probability - observed_rate)
        weighted_gap += len(selected) / len(items) * gap
        max_gap = max(max_gap, gap)
        bins.append(CalibrationBin(lower, upper, len(selected), mean_probability, observed_rate, gap))
    accuracy = sum((case.probability >= 0.5) == case.observed for case in items) / len(items)
    payload = {
        "cases": [asdict(case) for case in items],
        "logical": logical,
        "materialized": materialized,
        "bins": [asdict(item) for item in bins],
    }
    return CalibrationReport(
        logical_cases=logical,
        materialized_cases=materialized,
        executed_cases=len(items),
        software_tested_cases=len(items),
        scientifically_verified_cases=0,
        brier_score=brier,
        log_loss=log_loss,
        expected_calibration_error=weighted_gap,
        maximum_calibration_error=max_gap,
        accuracy_at_half=accuracy,
        bins=tuple(bins),
        digest=_digest(payload),
    )


def deterministic_re1024_fixture() -> tuple[CalibrationCase, ...]:
    """Create 1,024 deterministic software cases; no external experiment occurs."""
    cases: list[CalibrationCase] = []
    for index in range(1024):
        family_index = index % 16
        perturbation = (index // 16) % 16
        latent = ((family_index * 17 + perturbation * 11 + index) % 101) / 100.0
        probability = min(0.99, max(0.01, 0.1 + 0.8 * latent))
        observed = ((index * 37 + family_index * 13 + perturbation * 7) % 100) < int(probability * 100)
        cases.append(
            CalibrationCase(
                case_id=f"re1024-{index:04d}",
                probability=round(probability, 6),
                observed=observed,
                family=f"family-{family_index:02d}",
            )
        )
    return tuple(cases)


def progressive_windows(cases: Sequence[CalibrationCase], window_sizes: Iterable[int]) -> tuple[CalibrationReport, ...]:
    reports: list[CalibrationReport] = []
    for size in window_sizes:
        if size <= 0 or size > len(cases):
            raise ValueError("window size outside case range")
        reports.append(
            calibrate(
                cases[:size],
                logical_cases=len(cases),
                materialized_cases=len(cases),
            )
        )
    return tuple(reports)
