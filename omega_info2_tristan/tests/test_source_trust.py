from omega_info2 import SourceTrustInput, score_source


def test_primary_traceable_source_scores_higher_than_opaque_source():
    strong = score_source(
        SourceTrustInput(
            reputation=0.9,
            traceability=0.9,
            reproducibility=0.8,
            freshness=0.8,
            independence=0.8,
            conflict_of_interest=0.0,
            opacity=0.0,
            primary_source=True,
            peer_reviewed=True,
        )
    )
    weak = score_source(
        SourceTrustInput(
            reputation=0.2,
            traceability=0.1,
            reproducibility=0.1,
            freshness=0.2,
            independence=0.2,
            conflict_of_interest=0.8,
            opacity=0.9,
        )
    )
    assert 0.0 <= weak <= 1.0
    assert 0.0 <= strong <= 1.0
    assert strong > weak
