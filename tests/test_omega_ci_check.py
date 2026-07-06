from omega_ci_check import ci_gate


def test_ci_gate_ok():
    assert ci_gate(True, 0) == "ok"


def test_ci_gate_review():
    assert ci_gate(True, 2) == "review"


def test_ci_gate_blocked():
    assert ci_gate(False, 0) == "blocked"
