from omega_learn_t.bayes_mastery import mastery_vector
from omega_learn_t.core import Evidence, MasteryAxis, SkillSpec
from omega_learn_t.cvcd import extract_invariants
from omega_learn_t.sage_learning_coach import SageLearningCoach


def test_mastery_vector_uses_evidence():
    scores = mastery_vector([
        Evidence(axis=MasteryAxis.UNDERSTANDING, successes=8, failures=0),
        Evidence(axis=MasteryAxis.SPEED, successes=0, failures=8),
    ])
    assert scores[MasteryAxis.UNDERSTANDING] > 0.7
    assert scores[MasteryAxis.SPEED] < 0.3


def test_cvcd_extracts_invariants():
    sig = extract_invariants("omega omega resonance phase RLC energy energy F=-kx")
    assert "omega" in sig.invariants
    assert sig.compression_ratio > 0


def test_coach_report_has_oakbench():
    spec = SkillSpec.from_mapping({
        "skill": "test skill",
        "goal": "learn test skill",
        "notes": "invariant invariant transfer residue",
        "evidence": [{"axis": "recall", "successes": 2, "failures": 1}],
    })
    report = SageLearningCoach().inspect(spec)
    assert "oakbench" in report
    assert "next_actions" in report
    assert report["skill"] == "test skill"
