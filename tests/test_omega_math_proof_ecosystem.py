from omega_math_proof_research_os.contracts import MathArtifact
from omega_math_proof_research_os.ecosystem import make_evidence_receipt, make_work_unit


def test_work_unit_does_not_claim_execution_success():
    unit = make_work_unit(work_unit_id="wu:test", source_count=5)
    assert unit["kind"] == "math_proof_research"
    assert unit["source_count"] == 5
    assert "not proof" in unit["claim_boundary"]


def test_receipt_separates_extraction_kernel_and_oak_counts():
    artifacts = [
        MathArtifact(artifact_id="a", kind="theorem", natural_text="A", oak_status="hold"),
        MathArtifact(
            artifact_id="b",
            kind="theorem",
            natural_text="B",
            formal_status="kernel_accepted",
            oak_status="verified",
        ),
    ]
    receipt = make_evidence_receipt(receipt_id="r:test", artifacts=artifacts, kernel_accepted=1)
    assert receipt["counts"] == {
        "source_extracted_artifacts": 2,
        "kernel_accepted": 1,
        "oak_verified": 1,
    }
