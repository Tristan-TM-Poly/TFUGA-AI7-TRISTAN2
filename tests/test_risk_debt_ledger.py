from tools.risk_debt_ledger import DebtSeverity, assess_risk_debt


def test_no_debt_is_low_and_allows_zero_touch():
    report = assess_risk_debt()
    assert report.total_points == 0
    assert report.severity == DebtSeverity.LOW
    assert not report.blocks_zero_touch


def test_missing_tests_creates_medium_debt():
    report = assess_risk_debt(missing_tests=True)
    assert report.total_points == 3
    assert report.severity == DebtSeverity.MEDIUM
    assert report.items[0].name == "missing_tests"


def test_no_rollback_blocks_zero_touch_when_high():
    report = assess_risk_debt(no_rollback=True, missing_tests=True)
    assert report.severity == DebtSeverity.HIGH
    assert report.blocks_zero_touch


def test_public_irreversible_side_effect_is_critical():
    report = assess_risk_debt(irreversible_or_public_side_effect=True, no_rollback=True)
    assert report.severity == DebtSeverity.CRITICAL
    assert report.blocks_zero_touch
