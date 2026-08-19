from tools.proof_ladder import ProofLevel, assess_proof_level, evidence_gap


def test_no_evidence_is_p0():
    assessment = assess_proof_level()
    assert assessment.level == ProofLevel.P0_NO_EVIDENCE
    assert "example" in assessment.required_next


def test_toy_test_is_p3():
    assessment = assess_proof_level(has_toy_test=True)
    assert assessment.level == ProofLevel.P3_TOY_TEST


def test_baseline_comparison_is_p5():
    assessment = assess_proof_level(compared_to_baseline=True)
    assert assessment.level == ProofLevel.P5_BASELINE_COMPARISON


def test_robust_standard_requires_reviewed_real_use():
    assessment = assess_proof_level(robust_standard=True, controlled_real_use=True, externally_reviewed=True)
    assert assessment.level == ProofLevel.P10_ROBUST_STANDARD


def test_evidence_gap():
    assert evidence_gap(ProofLevel.P2_EXAMPLE, ProofLevel.P5_BASELINE_COMPARISON) == 3
    assert evidence_gap(ProofLevel.P8_EXTERNAL_REVIEW, ProofLevel.P4_BENCHMARK) == 0
