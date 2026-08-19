from tools.proof_capital import calculate_proof_capital


def test_negative_capital_blocks_upgrade():
    report = calculate_proof_capital(overclaims=2, risk_debt_points=5)
    assert report.capital < 0
    assert not report.can_upgrade_claim


def test_moderate_capital_can_upgrade_without_overclaims():
    report = calculate_proof_capital(tests=3, measurements=2, strong_sources=2)
    assert report.capital >= 10
    assert report.can_upgrade_claim


def test_overclaims_block_upgrade_even_with_capital():
    report = calculate_proof_capital(tests=10, overclaims=1)
    assert report.capital > 0
    assert not report.can_upgrade_claim
