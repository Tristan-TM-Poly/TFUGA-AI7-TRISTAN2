from omega_game.engines import LanguageGMRubric, LanguageQuest, LanguageRubricScores, PolyglotLanguageEngine
from omega_game.engines.language_gm_rubric import LanguageGMEvaluation


def _run_for(target_style: str):
    quest = LanguageQuest(
        source_text="Explain this module for review.",
        source_language="en",
        target_style=target_style,
        audience="repo reviewer",
        intent="document behavior and limits",
        constraints=["limits visible"],
    )
    return PolyglotLanguageEngine().transform(quest)


def test_language_gm_rubric_evaluates_markdown_run():
    run = _run_for("markdown_doc")
    evaluation = LanguageGMRubric().evaluate(run)

    assert evaluation.target_style == "markdown_doc"
    assert 0.0 <= evaluation.score <= 1.0
    assert evaluation.level in {"needs_practice", "apprentice", "builder", "strategist", "master"}
    assert "markdown_doc_format_fit" in evaluation.m_plus


def test_language_gm_rubric_detects_json_format_fit():
    run = _run_for("json_contract")
    evaluation = LanguageGMRubric().evaluate(run)

    assert evaluation.scores.format_fit >= 0.80
    assert evaluation.next_training_quest in {"create_second_audience_variant", "repeat_with_tighter_intent"}


def test_language_rubric_scores_are_bounded():
    scores = LanguageRubricScores(
        clarity=0.8,
        structure=0.8,
        audience_fit=0.8,
        format_fit=0.8,
        oak_safety=0.9,
        intent_preservation=0.7,
        drift=0.1,
        hidden_claims=0.0,
    )

    assert 0.0 <= scores.score() <= 1.0
    assert scores.level() in {"needs_practice", "apprentice", "builder", "strategist", "master"}
    assert scores.to_dict()["score"] == scores.score()


def test_language_rubric_rejects_bad_score_value():
    try:
        LanguageRubricScores(
            clarity=2.0,
            structure=0.8,
            audience_fit=0.8,
            format_fit=0.8,
            oak_safety=0.8,
            intent_preservation=0.8,
        )
    except ValueError as exc:
        assert "clarity" in str(exc)
    else:
        raise AssertionError("LanguageRubricScores accepted out-of-range clarity")


def test_language_gm_evaluation_serializes():
    run = _run_for("yaml_plan")
    evaluation = LanguageGMRubric().evaluate(run)
    payload = evaluation.to_dict()

    assert set(payload) == {
        "target_style",
        "audience",
        "score",
        "level",
        "scores",
        "m_plus",
        "m_minus",
        "next_training_quest",
    }
    assert payload["scores"]["score"] == payload["score"]


def test_language_gm_rubric_many_preserves_count():
    rubric = LanguageGMRubric()
    runs = [_run_for("en_clear"), _run_for("markdown_doc")]
    evaluations = rubric.evaluate_many(runs)

    assert len(evaluations) == 2
    assert all(isinstance(item, LanguageGMEvaluation) for item in evaluations)
