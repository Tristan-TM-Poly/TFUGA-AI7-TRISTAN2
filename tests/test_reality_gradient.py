from tools.reality_gradient import RealityLevel, assess_reality_level, forbid_overclaim


def test_unanchored_idea_is_vision():
    assessment = assess_reality_level()
    assert assessment.level == RealityLevel.R1_VISION
    assert "RealityAnchor" in assessment.next_upgrade


def test_metaphor_level_from_metaphor_only():
    assessment = assess_reality_level(has_metaphor_only=True)
    assert assessment.level == RealityLevel.R2_METAPHOR


def test_prototype_and_local_test_levels():
    assert assess_reality_level(has_prototype=True).level == RealityLevel.R5_PROTOTYPE
    assert assess_reality_level(has_local_test=True).level == RealityLevel.R6_LOCAL_TEST


def test_reproduction_and_canon_levels():
    assert assess_reality_level(has_reproduction=True).level == RealityLevel.R8_REPRODUCTION
    assert assess_reality_level(has_reproduction=True, canon_reviewed=True).level == RealityLevel.R9_REINFORCED_CANON


def test_forbid_overclaim_detects_r2_claiming_r10():
    assert forbid_overclaim(RealityLevel.R2_METAPHOR, RealityLevel.R10_PROOF_OR_STANDARD)
    assert not forbid_overclaim(RealityLevel.R7_MEASUREMENT, RealityLevel.R3_HYPOTHESIS)
