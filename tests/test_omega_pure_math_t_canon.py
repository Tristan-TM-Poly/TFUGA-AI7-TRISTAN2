from omega_pure_math_t.canon import BRANCH_CANON, canon_summary, validate_canon


def test_pure_math_branch_canon_is_unique_and_machine_valid():
    assert not validate_canon()
    identifiers = [branch.identifier for branch in BRANCH_CANON]
    assert len(identifiers) == len(set(identifiers))
    assert len(identifiers) >= 50


def test_canon_has_executable_and_research_program_layers():
    summary = canon_summary()
    assert summary["valid"]
    assert summary["status_counts"]["executable"] >= 10
    assert summary["status_counts"]["research-program"] >= 10
