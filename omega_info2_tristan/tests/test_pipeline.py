from omega_info2 import EvidenceVector, Info2Pipeline


def test_info2_pipeline_runs_end_to_end():
    result = Info2Pipeline().run_text(
        "Every useful information object should carry provenance, uncertainty, action, OAK status and residue.",
        source="test:theory_note",
        domain="meta-information",
        evidence=[EvidenceVector(label="structured design review", truth_lr=1.5, utility_lr=2.0, source="review:001")],
    )
    payload = result.to_dict()
    assert payload["info_object"]["claims"]
    assert payload["cvcd_report"]["invariants"]
    assert payload["graph"]["nodes"]
    assert result.info_object.action.recommended_route is not None
