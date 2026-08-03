"""Cross-run calibration receipts with append-only deterministic chaining."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping

GENESIS = "sha256:" + "0" * 64


@dataclass(frozen=True)
class CalibrationRun:
    run_id: str
    dataset_digest: str
    model_digest: str
    case_count: int
    brier_score: float
    log_loss: float
    expected_calibration_error: float
    scientifically_verified_cases: int = 0


@dataclass(frozen=True)
class CalibrationReceipt:
    sequence: int
    run: CalibrationRun
    previous_digest: str
    receipt_digest: str
    trend: str
    claim: str = "software_calibration_receipt_only"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def validate_run(run: CalibrationRun) -> None:
    if not run.run_id.strip() or not run.dataset_digest.startswith("sha256:") or not run.model_digest.startswith("sha256:"):
        raise ValueError("invalid run identity")
    if run.case_count <= 0 or run.scientifically_verified_cases < 0:
        raise ValueError("invalid case counts")
    for value in (run.brier_score, run.log_loss, run.expected_calibration_error):
        if not math.isfinite(value) or value < 0:
            raise ValueError("metrics must be finite and non-negative")


def classify_trend(previous: CalibrationRun | None, current: CalibrationRun, tolerance: float = 1e-12) -> str:
    if previous is None:
        return "baseline"
    deltas = (
        current.brier_score - previous.brier_score,
        current.log_loss - previous.log_loss,
        current.expected_calibration_error - previous.expected_calibration_error,
    )
    if all(delta < -tolerance for delta in deltas):
        return "improved"
    if all(delta > tolerance for delta in deltas):
        return "degraded"
    if all(abs(delta) <= tolerance for delta in deltas):
        return "stable"
    return "mixed"


def build_chain(runs: Iterable[CalibrationRun], *, genesis: str = GENESIS) -> tuple[CalibrationReceipt, ...]:
    previous_digest = genesis
    previous_run: CalibrationRun | None = None
    receipts: list[CalibrationReceipt] = []
    seen: set[str] = set()
    for sequence, run in enumerate(runs):
        validate_run(run)
        if run.run_id in seen:
            raise ValueError("duplicate run id")
        seen.add(run.run_id)
        trend = classify_trend(previous_run, run)
        unsigned = {
            "sequence": sequence,
            "run": asdict(run),
            "previous_digest": previous_digest,
            "trend": trend,
        }
        receipt_digest = _digest(unsigned)
        receipts.append(CalibrationReceipt(sequence, run, previous_digest, receipt_digest, trend))
        previous_digest = receipt_digest
        previous_run = run
    return tuple(receipts)


def verify_chain(receipts: Iterable[CalibrationReceipt], *, genesis: str = GENESIS) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    previous_digest = genesis
    previous_run: CalibrationRun | None = None
    for index, receipt in enumerate(receipts):
        try:
            validate_run(receipt.run)
        except ValueError as exc:
            errors.append(f"invalid_run:{index}:{exc}")
        if receipt.sequence != index:
            errors.append(f"sequence:{index}")
        if receipt.previous_digest != previous_digest:
            errors.append(f"previous:{index}")
        expected_trend = classify_trend(previous_run, receipt.run)
        if receipt.trend != expected_trend:
            errors.append(f"trend:{index}")
        expected = _digest({"sequence": index, "run": asdict(receipt.run), "previous_digest": previous_digest, "trend": expected_trend})
        if receipt.receipt_digest != expected:
            errors.append(f"digest:{index}")
        previous_digest = receipt.receipt_digest
        previous_run = receipt.run
    return not errors, tuple(errors)


def compare_run_sets(left: Iterable[CalibrationReceipt], right: Iterable[CalibrationReceipt]) -> Mapping[str, object]:
    left_items, right_items = tuple(left), tuple(right)
    left_valid, left_errors = verify_chain(left_items)
    right_valid, right_errors = verify_chain(right_items)
    common = min(len(left_items), len(right_items))
    first_divergence = next((index for index in range(common) if left_items[index].receipt_digest != right_items[index].receipt_digest), None)
    if first_divergence is None and len(left_items) != len(right_items):
        first_divergence = common
    return {
        "left_valid": left_valid,
        "right_valid": right_valid,
        "left_errors": left_errors,
        "right_errors": right_errors,
        "first_divergence": first_divergence,
        "identical": first_divergence is None,
    }
