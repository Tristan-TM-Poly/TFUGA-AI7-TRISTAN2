from omega_thesis_factory_t.claim_style import claim_mode, safer_claim


def test_early_status_is_hypothesis():
    assert claim_mode("B") == "hypothesis"


def test_mid_status_is_tested():
    assert claim_mode("D") == "tested"


def test_safer_claim_prefixes_text():
    assert safer_claim("C", "demo").startswith("Hypothesis:")
