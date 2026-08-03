from tools.canon_rank import CanonRank, assess_canon_rank


def test_raw_fragment_is_c0():
    assessment = assess_canon_rank()
    assert assessment.rank == CanonRank.C0_RAW_FRAGMENT
    assert "capture" in assessment.next_upgrade


def test_tested_tool_is_c6():
    assessment = assess_canon_rank(tested_tool=True)
    assert assessment.rank == CanonRank.C6_TESTED_TOOL


def test_fundamental_requires_reinforced_and_reproduced():
    assessment = assess_canon_rank(fundamental=True, reinforced=True, reproduced=True)
    assert assessment.rank == CanonRank.C10_FUNDAMENTAL_PILLAR
