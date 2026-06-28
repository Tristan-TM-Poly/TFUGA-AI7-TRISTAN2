from omega_unc2_t import (
    U2Claim,
    domain_shift_score,
    expected_calibration_error,
    meta_calibration_error,
    oak_u2_gate,
    oak_u2_score,
    residual_of_uncertainty,
)


def test_oak_u2_score_and_gate_flag_high_meta_uncertainty():
    claim = U2Claim(
        claim="Untested revenue claim",
        uncertainty_u1={"market": 0.8, "execution": 0.7},
        meta_uncertainty_u2={"sales_gap": 0.9, "comparables": 0.7},
        evidence_strength=0.2,
        residual_score=0.5,
        decision_cost=0.8,
        reversibility=0.2,
        fertility=0.9,
        value=0.8,
        metadata={"displayed_confidence": 0.9},
    )

    score = oak_u2_score(claim)
    result = oak_u2_gate(score)

    assert score["u1"] > 0.7
    assert score["u2"] > 0.75
    assert result.status in {"RED", "ORANGE", "BLACK"}
    assert result.next_action


def test_calibration_metrics_are_bounded():
    ece1 = expected_calibration_error([0.1, 0.8, 0.9], [False, True, False], bins=3)
    ece2 = meta_calibration_error([0.2, 0.7, 0.9], [True, True, False], bins=3)
    assert 0.0 <= ece1 <= 1.0
    assert 0.0 <= ece2 <= 1.0


def test_residual_of_uncertainty_detects_overconfidence():
    diagnostics = residual_of_uncertainty([0.1, 0.5, 1.0], [0.2, 0.2, 0.4])
    assert diagnostics["coverage"] < 1.0
    assert diagnostics["mean_ru"] > 0.0


def test_domain_shift_score_combines_signals():
    score = domain_shift_score(
        {
            "out_of_domain": 0.8,
            "model_disagreement": 0.7,
            "residual_anomaly": 0.5,
            "source_gap": 0.6,
        }
    )
    assert 0.0 < score <= 1.0
