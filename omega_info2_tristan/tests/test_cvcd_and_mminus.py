from omega_info2 import CVCDCompressor, InfoObject, InfoScores, MMinusRegistry, OAKInfoGate


def test_cvcd_compressor_extracts_invariants_and_residue():
    text = "provenance uncertainty action provenance OAK CVCD evidence residue raretermx"
    report = CVCDCompressor(max_invariants=3).compress_text(text)
    labels = {item.label for item in report.invariants}
    assert "provenance" in labels
    assert report.compression_gain > 0
    assert report.residue


def test_cvcd_compressor_updates_info_object():
    obj = InfoObject.example()
    report = CVCDCompressor(max_invariants=5).compress_info_object(obj)
    assert obj.scores.compression_gain == report.compression_gain
    assert obj.provenance.transformations[-1].operation == "compress_cvcd_mvp"


def test_m_minus_registry_from_failed_oak_report():
    obj = InfoObject.example()
    obj.meta.source = None
    obj.scores = InfoScores(truth=0.3, utility=0.8, fertility=0.8, testability=0.2, risk=0.2, source_trust=0.1)
    report = OAKInfoGate().evaluate(obj)
    entries = MMinusRegistry.entries_from_oak_report(obj, report)
    registry = MMinusRegistry()
    registry.extend(entries)
    rules = registry.find_rules("source")
    assert entries
    assert any("source" in rule.lower() or "provenance" in rule.lower() for rule in rules)
