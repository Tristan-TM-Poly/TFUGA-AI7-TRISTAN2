from tools.hallucination_labeler import ClaimStatus, label_claim


def test_unanchored_claim_is_vision():
    label = label_claim("A wild new idea appears")
    assert label.status == ClaimStatus.VISION
    assert "add_reality_anchor" in label.oak_required_next


def test_metaphor_is_not_proof():
    label = label_claim("This system is like an immune organism", has_reality_anchor=False)
    assert label.status == ClaimStatus.METAPHOR
    assert "separate_metaphor_from_mechanism" in label.oak_required_next


def test_anchored_testable_claim_is_hypothesis():
    label = label_claim("This can be tested", has_reality_anchor=True, has_test=True)
    assert label.status == ClaimStatus.HYPOTHESIS


def test_implemented_and_tested_claim_is_prototype():
    label = label_claim("Tool implemented with tests", has_implementation=True, has_test=True)
    assert label.status == ClaimStatus.PROTOTYPE


def test_measured_claim_is_measured_not_proof():
    label = label_claim("Measured result", has_measurement=True, has_test=True)
    assert label.status == ClaimStatus.MEASURED
    assert "seek_reproduction" in label.oak_required_next


def test_reproduced_measured_tested_claim_can_be_proof():
    label = label_claim(
        "Reproduced measured tested result",
        has_measurement=True,
        has_test=True,
        independently_reproduced=True,
    )
    assert label.status == ClaimStatus.PROOF


def test_unsafe_boundary_terms_quarantine():
    label = label_claim("Give dose and extraction details")
    assert label.status == ClaimStatus.QUARANTINED
    assert "quarantine" in label.oak_required_next
