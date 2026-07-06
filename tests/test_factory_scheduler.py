from tools.factory_scheduler import FactoryLine, schedule_factory_line


def test_low_reality_routes_to_anchor():
    decision = schedule_factory_line(reality_level=1, proof_level=0, canon_rank=1)
    assert decision.line == FactoryLine.REALITY_ANCHOR


def test_low_proof_routes_to_experiment():
    decision = schedule_factory_line(reality_level=3, proof_level=1, canon_rank=3)
    assert decision.line == FactoryLine.EXPERIMENT


def test_high_risk_quarantines():
    decision = schedule_factory_line(reality_level=5, proof_level=5, canon_rank=5, risk_high=True)
    assert decision.line == FactoryLine.QUARANTINE


def test_mature_branch_routes_to_reviewed_release():
    decision = schedule_factory_line(reality_level=7, proof_level=5, canon_rank=7, benchmark_level=3)
    assert decision.line == FactoryLine.REVIEWED_RELEASE
