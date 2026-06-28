from omega_game.engines import LanguageRepairLoop, RepairAction, RepairAttempt, default_language_repair_loop
from omega_game.engines.language_validators import LanguageValidators
from omega_game.engines.polyglot_language import LanguageRun


def _run(target_style="markdown_doc"):
    return LanguageRun(
        target_style=target_style,
        audience="repo reviewer",
        draft="draft",
        clarity_score=0.2,
        safety_score=0.2,
        structure_score=0.1,
        oak_notes=[],
        m_plus=[],
        m_minus=[],
        next_quest="revise",
    )


def test_loop_reaches_markdown_target():
    result = default_language_repair_loop().repair(_run("markdown_doc"), target_score=0.80, max_attempts=3)

    assert result.converged is True
    assert result.final_report.score >= 0.80
    assert result.attempts
    assert result.next_action == "none"


def test_loop_reaches_json_target():
    result = LanguageRepairLoop().repair(_run("json_contract"), target_score=0.80, max_attempts=2)

    assert result.converged is True
    assert result.final_report.valid is True
    assert "intent" in result.final_run.draft


def test_loop_reaches_yaml_target():
    result = LanguageRepairLoop().repair(_run("yaml_plan"), target_score=0.80, max_attempts=2)

    assert result.converged is True
    assert "status:" in result.final_run.draft
    assert "oak:" in result.final_run.draft


def test_loop_reaches_issue_target():
    result = LanguageRepairLoop().repair(_run("github_issue"), target_score=0.80, max_attempts=2)

    assert result.converged is True
    assert "## Goal" in result.final_run.draft
    assert "## Notes" in result.final_run.draft


def test_loop_with_zero_attempts_keeps_initial_state():
    result = LanguageRepairLoop().repair(_run("markdown_doc"), target_score=0.80, max_attempts=0)

    assert result.converged is False
    assert result.attempts == []
    assert result.next_action.startswith("repair_")


def test_attempt_requires_positive_index():
    report = LanguageValidators().validate(_run("markdown_doc"))
    try:
        RepairAttempt(index=0, before_score=0.0, after_score=0.0, actions=[RepairAction("x", "y")], report_after=report)
    except ValueError as exc:
        assert "index" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_loop_result_serializes():
    result = LanguageRepairLoop().repair(_run("markdown_doc"), target_score=0.80, max_attempts=3)
    payload = result.to_dict()

    assert set(payload) == {
        "target_score",
        "converged",
        "final_run",
        "final_report",
        "attempts",
        "m_plus",
        "m_minus",
        "next_action",
    }
    assert payload["final_report"]["score"] >= 0.80
