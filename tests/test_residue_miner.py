from tools.residue_miner import ResidueStatus, mine_residue


def test_raw_residue_stays_raw_without_pattern():
    packet = mine_residue("unexplained signal")
    assert packet.status == ResidueStatus.RAW


def test_patterned_residue_becomes_testable():
    packet = mine_residue("recurring failure mode", has_pattern=True)
    assert packet.status == ResidueStatus.TESTABLE
    assert "falsifiable test" in packet.safe_next_action


def test_review_scoped_residue_quarantines():
    packet = mine_residue("review scoped residue", sensitive=True)
    assert packet.status == ResidueStatus.QUARANTINED
