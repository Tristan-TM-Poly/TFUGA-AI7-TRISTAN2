from tools.canon_thermostat import CanonTemperature, assess_canon_temperature


def test_unlinked_branch_is_frozen():
    report = assess_canon_temperature()
    assert report.temperature == CanonTemperature.T0_FROZEN


def test_active_testable_branch_is_fertile():
    report = assess_canon_temperature(active=True, testable=True)
    assert report.temperature == CanonTemperature.T2_FERTILE


def test_high_novelty_without_testability_is_hot():
    report = assess_canon_temperature(high_novelty=True, testable=False)
    assert report.temperature == CanonTemperature.T3_HOT


def test_overclaim_overheats():
    report = assess_canon_temperature(overclaim=True)
    assert report.temperature == CanonTemperature.T4_OVERHEATED
