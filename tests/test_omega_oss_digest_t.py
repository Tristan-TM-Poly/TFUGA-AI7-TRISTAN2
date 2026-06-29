from datetime import date

from omega_oss_digest_t.license_gate import classify_license
from omega_oss_digest_t.oak_runner import oak_decision
from omega_oss_digest_t.scorer import DigestScore, score_band
from omega_oss_digest_t.stackoverflow_attribution import build_attribution, stackoverflow_license_for_date


def test_mit_is_green():
    d = classify_license("MIT")
    assert d.oak_status == "OAK_GREEN_USE"
    assert d.commercial_use_possible is True


def test_no_license_blocks_reuse():
    d = classify_license("NOASSERTION")
    assert d.oak_status == "OAK_RED_LICENSE"
    assert "blocked" in d.direct_code_reuse


def test_stackoverflow_cc_is_rewrite_first():
    d = classify_license("CC-BY-SA-4.0")
    assert d.sharealike_risk == "high"
    assert d.oak_status == "OAK_YELLOW_REWRITE_ONLY"


def test_score_band_green():
    s = DigestScore(
        fit=1,
        license_compatibility=1,
        tests=1,
        security=1,
        maintainability=1,
        cvcd_compressibility=1,
        utility=1,
        community_activity=1,
        risk=0,
    )
    assert s.value() == 1.0
    assert score_band(s.value()) == "OAK_GREEN_CANON"


def test_oak_blocks_missing_license():
    decision = oak_decision("NOASSERTION", DigestScore())
    assert decision.status == "OAK_RED_BLOCKED"


def test_stackoverflow_license_dates():
    assert stackoverflow_license_for_date(date(2010, 1, 1)) == "CC-BY-SA-2.5"
    assert stackoverflow_license_for_date(date(2015, 1, 1)) == "CC-BY-SA-3.0"
    assert stackoverflow_license_for_date(date(2019, 1, 1)) == "CC-BY-SA-4.0"


def test_attribution_text_contains_license():
    a = build_attribution(1, "Example", "https://stackoverflow.com/q/1", date(2020, 1, 1), "alice")
    assert "CC-BY-SA-4.0" in a.attribution_text
