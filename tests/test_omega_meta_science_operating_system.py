from omega_meta_science_t.operating_system import (
    BuildNode,
    ClaimCertificate,
    DiscoveryROIInput,
    EvidenceRecord,
    ScientificBuildGraph,
    ScientificClaim,
    TheorySnapshot,
    VerifiedDiscoveryMetrics,
    check_claim_type,
    discovery_roi,
    run_discovery_os_demo,
    theory_diff,
    validate_claim_certificate,
    verified_discovery_unit,
)


def test_type_system_rejects_correlation_to_causal_without_design():
    evidence = {"E1": EvidenceRecord("E1", "observation", "fixture")}
    claim = ScientificClaim(
        "C1",
        "x and y co-vary",
        "correlation",
        "fixture",
        "fixture",
        0.2,
        ("E1",),
    )
    report = check_claim_type(claim, evidence, target_kind="causal")
    assert not report.allowed
    assert "causal_claim_requires_causal_design" in report.blockers


def test_type_system_accepts_declared_causal_design():
    evidence = {
        "E1": EvidenceRecord("E1", "observation", "fixture"),
        "E2": EvidenceRecord("E2", "causal_design", "fixture"),
    }
    claim = ScientificClaim(
        "C1",
        "intervention changes outcome",
        "correlation",
        "fixture",
        "fixture",
        0.1,
        ("E1", "E2"),
    )
    report = check_claim_type(claim, evidence, target_kind="causal")
    assert report.allowed


def test_theory_diff_separates_change_classes():
    old = TheorySnapshot("T", "1", ("a", "b"), ("L1",), "D", ("E1",), ("R1",))
    new = TheorySnapshot("T", "2", ("a",), ("L1", "L2"), "D", ("E1", "E2"), ("R1", "R2"))
    report = theory_diff(old, new)
    assert report.assumptions_removed == ("b",)
    assert report.laws_added == ("L2",)
    assert report.evidence_added == ("E2",)
    assert report.representations_added == ("R2",)
    assert set(report.change_classes) == {
        "assumption_change",
        "model_change",
        "evidence_change",
        "representation_change",
    }


def test_build_graph_transitive_invalidation():
    graph = ScientificBuildGraph(
        (
            BuildNode("instrument", "instrument"),
            BuildNode("dataset", "dataset", ("instrument",)),
            BuildNode("model", "model", ("dataset",)),
            BuildNode("claim", "claim", ("model",)),
            BuildNode("unrelated", "note"),
        )
    )
    audit = graph.audit()
    assert audit.valid
    report = graph.invalidated_by(("dataset",))
    assert report.invalidated == ("claim", "dataset", "model")
    assert report.unaffected == ("instrument", "unrelated")


def test_build_graph_detects_cycle():
    graph = ScientificBuildGraph(
        (
            BuildNode("A", "claim", ("B",)),
            BuildNode("B", "model", ("A",)),
        )
    )
    audit = graph.audit()
    assert not audit.valid
    assert "dependency_cycle" in audit.blockers


def test_claim_certificate_fails_closed_without_tests():
    evidence = {"E": EvidenceRecord("E", "causal_design", "fixture")}
    claim = ScientificClaim(
        "C",
        "declared causal fixture",
        "correlation",
        "fixture",
        "fixture",
        0.1,
        ("E",),
    )
    report = validate_claim_certificate(
        ClaimCertificate(claim, "causal", "PASS", ()),
        evidence,
    )
    assert not report.certified
    assert "missing_tests" in report.blockers


def test_vdu_and_roi_are_bounded_decision_metrics():
    vdu = verified_discovery_unit(
        VerifiedDiscoveryMetrics(0.8, 0.9, 0.6, 0.7, 0.4, True)
    )
    assert 0.0 < vdu.score <= 1.0
    blocked = verified_discovery_unit(
        VerifiedDiscoveryMetrics(1.0, 1.0, 1.0, 1.0, 1.0, False)
    )
    assert blocked.score == 0.0

    roi = discovery_roi(DiscoveryROIInput(100.0, 0.4, 5.0, 20.0, 10.0, 5.0))
    assert roi.expected_validated_value == 40.0
    assert roi.total_cost == 40.0
    assert roi.roi == 1.0


def test_composed_r0_4_demo():
    report = run_discovery_os_demo()
    assert not report.rejected_promotion.allowed
    assert report.accepted_promotion.allowed
    assert report.build_audit.valid
    assert report.claim_certificate.certified
    assert report.invalidation.invalidated == ("artifact", "claim", "dataset", "model")
    assert report.vdu.score > 0.0
    assert report.roi.roi == 1.0
