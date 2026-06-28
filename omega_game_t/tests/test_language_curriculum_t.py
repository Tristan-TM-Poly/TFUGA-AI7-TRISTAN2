from omega_game.engines import CurriculumQuest, CurriculumTrack, LanguageCurriculum, default_language_curriculum


def test_curriculum_tracks_are_valid():
    curriculum = default_language_curriculum()
    tracks = curriculum.tracks()

    assert len(tracks) == 9
    assert {track.name for track in tracks} >= {"fr_clear", "en_clear", "markdown_doc", "json_contract", "yaml_plan"}
    assert all(track.required_skills for track in tracks)


def test_curriculum_track_rejects_bad_mapping():
    try:
        CurriculumTrack("markdown_doc", "yaml_plan", "bad", ["structure"])
    except ValueError as exc:
        assert "target_style" in str(exc)
    else:
        raise AssertionError("CurriculumTrack accepted mismatched target_style")


def test_quests_for_track_create_language_quests():
    curriculum = LanguageCurriculum()
    quest = curriculum.quests_for_track("github_issue")[0]
    language_quest = quest.to_language_quest()

    assert language_quest.target_style == "github_issue"
    assert language_quest.audience == "new contributor"


def test_curriculum_quest_rejects_bad_threshold():
    try:
        CurriculumQuest(
            quest_id="bad",
            track="en_clear",
            level="apprentice",
            source_text="x",
            audience="builder",
            intent="explain",
            pass_threshold=2.0,
        )
    except ValueError as exc:
        assert "pass_threshold" in str(exc)
    else:
        raise AssertionError("CurriculumQuest accepted bad pass_threshold")


def test_run_quest_returns_progress_contract():
    curriculum = default_language_curriculum()
    quest = curriculum.quests_for_track("markdown_doc")[0]
    progress = curriculum.run_quest(quest)
    payload = progress.to_dict()

    assert set(payload) == {"quest", "evaluation", "passed", "xp", "level_hint", "m_plus", "m_minus", "next_quest_id"}
    assert progress.xp >= 0
    assert progress.level_hint in {"apprentice", "builder", "verifier", "strategist", "master"}
    assert progress.next_quest_id


def test_evaluate_progress_empty_and_non_empty():
    curriculum = default_language_curriculum()
    empty = curriculum.evaluate_progress([])
    assert empty == {"count": 0, "average_score": 0.0, "passed": 0, "xp": 0, "level_hint": "apprentice"}

    progress = curriculum.run_quest(curriculum.quests_for_track("yaml_plan")[0])
    summary = curriculum.evaluate_progress([progress])
    assert summary["count"] == 1
    assert 0.0 <= summary["average_score"] <= 1.0
    assert summary["xp"] == progress.xp


def test_default_quests_cover_all_tracks():
    curriculum = default_language_curriculum()
    quests = curriculum.default_quests()
    tracks = {quest.track for quest in quests}

    assert len(quests) == 27
    assert tracks >= {"fr_clear", "en_clear", "teaching", "markdown_doc", "json_contract", "yaml_plan", "github_issue", "pitch", "ip_caution"}
