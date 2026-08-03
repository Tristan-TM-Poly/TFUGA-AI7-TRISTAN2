from tools.scope_guard import check_scope


def test_structure_note_allowed():
    decision = check_scope("move directory and update index")
    assert decision.allowed


def test_protected_note_not_allowed():
    decision = check_scope("edit boundary wording")
    assert not decision.allowed


def test_unclear_note_not_allowed():
    decision = check_scope("change system")
    assert not decision.allowed
