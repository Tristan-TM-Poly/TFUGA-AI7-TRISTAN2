import pytest

from omega_re_t.adversarial_workers_r05 import ExpectedLease, WorkerSubmission, audit_submissions
from omega_re_t.drift_monitor_r05 import (
    CalibrationSnapshot,
    compare_snapshots,
    jensen_shannon,
    monitor_sequence,
    population_stability_index,
)


def test_identical_distributions_have_zero_drift():
    distribution = {"a": 2, "b": 3}
    assert jensen_shannon(distribution, distribution) == pytest.approx(0.0)
    assert population_stability_index(distribution, distribution) == pytest.approx(0.0)


def test_drift_report_blocks_large_shift():
    reference = CalibrationSnapshot("a", {"low": 100, "high": 1}, 0.1, 0.01, 100)
    current = CalibrationSnapshot("b", {"low": 1, "high": 100}, 0.3, 0.2, 100)
    report = compare_snapshots(reference, current)
    assert report.severity == "block"
    assert "distribution_shift" in report.reasons
    assert "calibration_degraded" in report.reasons


def test_monitor_sequence_requires_two_snapshots():
    snapshot = CalibrationSnapshot("a", {"x": 1}, 0.1, 0.01, 10)
    with pytest.raises(ValueError):
        monitor_sequence((snapshot,))


def test_monitor_sequence_returns_adjacent_reports():
    a = CalibrationSnapshot("a", {"x": 9, "y": 1}, 0.1, 0.01, 10)
    b = CalibrationSnapshot("b", {"x": 8, "y": 2}, 0.11, 0.02, 10)
    c = CalibrationSnapshot("c", {"x": 7, "y": 3}, 0.12, 0.03, 10)
    reports = monitor_sequence((a, b, c))
    assert [(item.reference_window, item.current_window) for item in reports] == [("a", "b"), ("b", "c")]


def test_snapshot_cannot_claim_scientific_verification():
    with pytest.raises(ValueError):
        CalibrationSnapshot("a", {"x": 1}, 0.1, 0.01, 10, scientifically_verified_cases=1)


def test_worker_audit_accepts_valid_submission():
    lease = ExpectedLease("item", "lease", "worker", "payload", 10)
    submission = WorkerSubmission("item", "lease", "worker", "payload", "result", 5)
    report = audit_submissions((lease,), (submission,))
    assert report.accepted_items == ("item",)
    assert report.rejected_count == 0


def test_worker_audit_detects_stale_and_mismatch():
    lease = ExpectedLease("item", "lease", "worker", "payload", 10)
    submission = WorkerSubmission("other", "lease", "intruder", "wrong", "result", 10)
    verdict = audit_submissions((lease,), (submission,)).verdicts[0]
    assert not verdict.accepted
    assert set(verdict.reasons) == {"item_mismatch", "worker_mismatch", "payload_digest_mismatch", "stale_lease"}


def test_worker_equivocation_is_detected():
    lease = ExpectedLease("item", "lease", "worker", "payload", 10)
    submissions = (
        WorkerSubmission("item", "lease", "worker", "payload", "result-a", 5),
        WorkerSubmission("item", "lease", "worker", "payload", "result-b", 6),
    )
    report = audit_submissions((lease,), submissions)
    assert report.equivocation_workers == ("worker",)
    assert "equivocation" in report.verdicts[1].reasons
    assert "duplicate_item_commit" in report.verdicts[1].reasons


def test_revoked_worker_is_blocked():
    lease = ExpectedLease("item", "lease", "worker", "payload", 10)
    submission = WorkerSubmission("item", "lease", "worker", "payload", "result", 5)
    verdict = audit_submissions((lease,), (submission,), revoked_workers=("worker",)).verdicts[0]
    assert verdict.reasons == ("revoked_worker",)
