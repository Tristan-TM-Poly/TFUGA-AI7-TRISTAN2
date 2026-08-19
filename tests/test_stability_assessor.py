from tools.stability_assessor import StabilityLevel, assess_stability


def test_low_score_is_s0():
    report = assess_stability()
    assert report.level == StabilityLevel.S0_LOW


def test_mid_score_is_checked_or_higher():
    report = assess_stability(load_checks=3, tests=3, docs=3)
    assert report.score == 9
    assert report.level >= StabilityLevel.S3_CHECKED


def test_issues_reduce_score():
    good = assess_stability(load_checks=5, tests=5, docs=5)
    lower = assess_stability(load_checks=5, tests=5, docs=5, issue_count=10)
    assert lower.score < good.score
