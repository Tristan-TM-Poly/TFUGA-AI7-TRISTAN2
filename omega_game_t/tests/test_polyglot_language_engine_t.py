from omega_game.engines import LanguageQuest, PolyglotLanguageEngine
from omega_game.engines.polyglot_language import LanguageRun


def test_polyglot_engine_creates_markdown_doc_run():
    quest = LanguageQuest(
        source_text="Explain the engine to a reviewer.",
        source_language="en",
        target_style="markdown_doc",
        audience="repo reviewer",
        intent="document behavior and limits",
    )
    run = PolyglotLanguageEngine().transform(quest)

    assert run.target_style == "markdown_doc"
    assert "# Draft" in run.draft
    assert 0.0 <= run.score <= 1.0
    assert "limits_visible" in run.oak_notes
    assert run.m_plus
    assert run.m_minus


def test_polyglot_engine_marks_sensitive_targets_for_review():
    quest = LanguageQuest(
        source_text="Prepare a cautious note about a new invention.",
        source_language="en",
        target_style="ip_caution",
        audience="internal reviewer",
        intent="preserve review status",
        constraints=["review required"],
    )
    run = PolyglotLanguageEngine().transform(quest)

    assert "human_review_before_external_use" in run.oak_notes
    assert "external_use_requires_review" in run.m_minus
    assert run.next_quest == "run_claims_and_review_pass"


def test_language_quest_rejects_empty_source():
    try:
        LanguageQuest(
            source_text="",
            source_language="en",
            target_style="en_clear",
            audience="builder",
            intent="explain",
        )
    except ValueError as exc:
        assert "source_text" in str(exc)
    else:
        raise AssertionError("LanguageQuest accepted empty source_text")


def test_language_quest_rejects_unsupported_target():
    try:
        LanguageQuest(
            source_text="hello",
            source_language="en",
            target_style="unsupported",
            audience="builder",
            intent="explain",
        )
    except ValueError as exc:
        assert "Unsupported target_style" in str(exc)
    else:
        raise AssertionError("LanguageQuest accepted unsupported target_style")


def test_language_run_score_is_bounded():
    run = LanguageRun(
        target_style="en_clear",
        audience="builder",
        draft="hello world",
        clarity_score=0.8,
        safety_score=0.9,
        structure_score=0.7,
        oak_notes=["limits_visible"],
        m_plus=["draft_created"],
        m_minus=["avoid_hidden_claims"],
        next_quest="create_second_audience_variant",
    )

    assert 0.0 <= run.score <= 1.0
    assert run.to_dict()["score"] == run.score


def test_default_quests_are_valid():
    engine = PolyglotLanguageEngine()
    quests = engine.default_quests()

    assert len(quests) >= 3
    assert all(engine.transform(quest).score >= 0.0 for quest in quests)
