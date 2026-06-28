from omega_info2 import InfoObject, InfoScores, OAKInfoGate, OAKStatus


def test_oak_gate_marks_ip_sensitive_when_ip_score_high():
    obj = InfoObject.example()
    obj.scores = InfoScores(
        truth=0.7,
        utility=0.8,
        fertility=0.9,
        testability=0.8,
        risk=0.2,
        source_trust=0.7,
        ip_sensitivity=0.9,
    )
    report = OAKInfoGate().evaluate(obj)
    assert report.status == OAKStatus.IP_SENSITIVE
    assert any("IP" in item for item in report.residue)


def test_oak_gate_does_not_canonize_missing_source():
    obj = InfoObject.example()
    obj.meta.source = None
    obj.scores = InfoScores(
        truth=0.9,
        utility=0.9,
        fertility=0.7,
        testability=0.8,
        risk=0.1,
        source_trust=0.8,
    )
    report = OAKInfoGate().evaluate(obj)
    assert "source_known" in report.checks_failed
    assert report.status != OAKStatus.CANONICAL
