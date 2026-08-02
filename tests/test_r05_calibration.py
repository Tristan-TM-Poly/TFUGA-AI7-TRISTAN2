import pytest

from omega_re_t.re1024_calibration_r05 import (
    CalibrationCase,
    calibrate,
    deterministic_re1024_fixture,
    progressive_windows,
)


def test_perfect_calibration_fixture():
    cases = (
        CalibrationCase("a", 0.0, False),
        CalibrationCase("b", 1.0, True),
    )
    report = calibrate(cases, bin_count=2)
    assert report.brier_score == 0.0
    assert report.accuracy_at_half == 1.0
    assert report.scientifically_verified_cases == 0


def test_re1024_fixture_is_deterministic_and_unique():
    first = deterministic_re1024_fixture()
    second = deterministic_re1024_fixture()
    assert first == second
    assert len(first) == 1024
    assert len({case.case_id for case in first}) == 1024


def test_re1024_calibration_preserves_claim_counts():
    cases = deterministic_re1024_fixture()
    report = calibrate(cases, logical_cases=1024, materialized_cases=1024)
    assert report.executed_cases == 1024
    assert report.software_tested_cases == 1024
    assert report.scientifically_verified_cases == 0
    assert report.digest.startswith("sha256:")
    assert 0.0 <= report.expected_calibration_error <= 1.0


def test_progressive_windows_are_monotonic_in_execution_count():
    cases = deterministic_re1024_fixture()
    reports = progressive_windows(cases, (64, 256, 1024))
    assert [item.executed_cases for item in reports] == [64, 256, 1024]
    assert all(item.logical_cases == 1024 for item in reports)


def test_invalid_probability_is_rejected():
    with pytest.raises(ValueError):
        CalibrationCase("bad", 1.1, True)


def test_declared_counts_cannot_understate_execution():
    cases = (CalibrationCase("a", 0.5, True), CalibrationCase("b", 0.5, False))
    with pytest.raises(ValueError):
        calibrate(cases, logical_cases=1)
