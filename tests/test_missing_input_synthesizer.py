from tools.missing_input_synthesizer import UncertaintyLevel, synthesize_missing_input


def test_reasonable_default_creates_test_or_simulation():
    plan = synthesize_missing_input("real benchmark")
    assert plan.uncertainty == UncertaintyLevel.MEDIUM
    assert plan.artifact_to_continue == "test_or_simulation"


def test_high_impact_creates_review_packet():
    plan = synthesize_missing_input("decision context", high_impact=True)
    assert plan.uncertainty == UncertaintyLevel.HIGH
    assert plan.artifact_to_continue == "review_packet"


def test_no_default_creates_assumptions_note():
    plan = synthesize_missing_input("unknown", has_reasonable_default=False)
    assert plan.artifact_to_continue == "assumptions_note"
