from omega_game.masters import (
    EvaluationRubric,
    GameMasterProfile,
    SkillScore,
    TrainingQuest,
    default_gamemaster_academy,
)


def test_academy_creates_default_profiles():
    academy = default_gamemaster_academy()
    profiles = academy.default_profiles()
    names = {profile.name for profile in profiles}

    assert {"RepoGM", "CodeGM", "EnergyGM", "ProcessGM", "RevenueGM", "LanguageGM"}.issubset(names)
    assert all(0.0 <= profile.average_skill() <= 1.0 for profile in profiles)


def test_profile_rejects_bad_level():
    try:
        GameMasterProfile(name="BadGM", domain="repo", level="bad", skills=[SkillScore("observe", 0.5)])
    except ValueError as exc:
        assert "level" in str(exc)
    else:
        raise AssertionError("GameMasterProfile accepted bad level")


def test_skill_score_rejects_out_of_range_score():
    try:
        SkillScore("observe", 2.0)
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError("SkillScore accepted out-of-range score")


def test_training_quest_rejects_bad_difficulty():
    try:
        TrainingQuest(name="quest", domain="repo", target_skill="observe", difficulty=2.0, prompt="x")
    except ValueError as exc:
        assert "difficulty" in str(exc)
    else:
        raise AssertionError("TrainingQuest accepted bad difficulty")


def test_evaluation_score_is_bounded_and_serializes():
    academy = default_gamemaster_academy()
    profile = academy.profile("RepoGM", "repo", "builder")
    quest = academy.quests_for("repo")[0]
    evaluation = academy.evaluate(profile, quest)
    payload = evaluation.to_dict()

    assert 0.0 <= evaluation.rubric.score() <= 1.0
    assert set(payload) == {"profile", "quest", "rubric", "passed", "next_level_hint", "m_plus", "m_minus", "next_quests"}
    assert payload["m_plus"]


def test_cross_domain_evaluation_penalizes_drift():
    academy = default_gamemaster_academy()
    profile = academy.profile("RepoGM", "repo", "builder")
    quest = academy.quests_for("energy")[0]
    evaluation = academy.evaluate(profile, quest)

    assert evaluation.rubric.drift >= 0.25
    assert evaluation.rubric.score() < 0.80


def test_rubric_rejects_out_of_range_value():
    try:
        EvaluationRubric(domain_skill=1.2, reasoning=0.5, safety=0.5, clarity=0.5, memory=0.5)
    except ValueError as exc:
        assert "domain_skill" in str(exc)
    else:
        raise AssertionError("EvaluationRubric accepted out-of-range value")
