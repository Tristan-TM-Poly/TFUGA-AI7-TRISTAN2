import pytest

from omega_thesis_factory_t import EvidenceVectorReceipt, MetricMeasurement, VECTOR_FIELDS


def _measurements(candidate_id: str, value: float, fixture: bool = False):
    costs = {"cost", "structural_debt", "proof_debt", "semantic_debt", "uncertainty", "irreversibility"}
    return tuple(
        MetricMeasurement(
            field=field,
            normalized_value=0.1 if field in costs else value,
            candidate_value=value,
            baseline_value=0.5,
            unit="score",
            direction="LOWER_BETTER" if field in costs else "HIGHER_BETTER",
            source_ref=f"run:{candidate_id}:{field}",
            baseline_ref=f"baseline:{candidate_id}:{field}",
            normalization_rule="explicit fixture normalization",
            synthetic_fixture=fixture,
        )
        for field in VECTOR_FIELDS
    )


def test_complete_receipt_preserves_explicit_vector():
    receipt = EvidenceVectorReceipt("OMEGA_TRANSFORM_T", _measurements("OMEGA_TRANSFORM_T", 0.8))
    assert receipt.complete
    assert not receipt.missing_fields
    assert receipt.vector().verified_value == 0.8
    assert receipt.to_dict()["score_inference_performed"] is False


def test_incomplete_receipt_cannot_be_vectorized():
    receipt = EvidenceVectorReceipt("OMEGA_TRANSFORM_T", _measurements("OMEGA_TRANSFORM_T", 0.8)[:1])
    assert not receipt.complete
    with pytest.raises(ValueError):
        receipt.vector()


def test_fixture_receipt_is_not_evidence_by_default():
    receipt = EvidenceVectorReceipt("OMEGA_TRANSFORM_T", _measurements("OMEGA_TRANSFORM_T", 0.8, fixture=True))
    assert not receipt.eligible_by_default
    with pytest.raises(ValueError):
        receipt.vector()


def test_baseline_provenance_is_required():
    m = MetricMeasurement("evidence", 0.5, 1.0, 0.5, "score", "HIGHER_BETTER", "run:x", "", "explicit")
    with pytest.raises(ValueError):
        m.validate()
