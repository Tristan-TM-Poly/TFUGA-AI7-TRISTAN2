from tools.failure_oracle import FailureSeverity, predict_failure_modes


def test_unknown_idea_has_low_unknown_unknowns():
    report = predict_failure_modes("Reality Forge artifact plan")
    assert report.highest_severity == FailureSeverity.LOW
    assert not report.no_touch_required


def test_medical_or_dose_terms_require_no_touch():
    report = predict_failure_modes("medical dose question")
    assert report.highest_severity == FailureSeverity.CRITICAL
    assert report.no_touch_required


def test_public_or_secret_terms_are_high_risk():
    report = predict_failure_modes("publish secret material")
    assert report.highest_severity == FailureSeverity.HIGH
    assert not report.no_touch_required


def test_overclaim_and_missing_tests_are_medium():
    report = predict_failure_modes("guaranteed result with no tests")
    assert report.highest_severity == FailureSeverity.MEDIUM
