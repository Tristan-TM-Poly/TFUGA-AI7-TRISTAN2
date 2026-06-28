from omega_game.engines import LanguageQuest, LanguageValidators, PolyglotLanguageEngine, ValidationCheck, ValidationReport
from omega_game.engines.polyglot_language import LanguageRun


def _run_for(target_style: str):
    quest = LanguageQuest(
        source_text="Document this module for review.",
        source_language="en",
        target_style=target_style,
        audience="repo reviewer",
        intent="show purpose, checks, and limits",
        constraints=["limits visible"],
    )
    return PolyglotLanguageEngine().transform(quest)


def test_markdown_validator_accepts_generated_markdown_doc():
    report = LanguageValidators().validate(_run_for("markdown_doc"))

    assert report.format_name == "markdown_doc"
    assert report.valid is True
    assert report.score >= 0.80
    assert "has_title_heading" in report.passed_checks
    assert "structure_validated" in report.m_plus


def test_json_contract_validator_accepts_generated_contract():
    report = LanguageValidators().validate(_run_for("json_contract"))

    assert report.valid is True
    assert "has_intent" in report.passed_checks
    assert "has_oak" in report.passed_checks


def test_yaml_plan_validator_accepts_generated_plan():
    report = LanguageValidators().validate(_run_for("yaml_plan"))

    assert report.valid is True
    assert "has_status" in report.passed_checks
    assert "has_oak_or_constraints" in report.passed_checks


def test_github_issue_validator_accepts_generated_issue():
    report = LanguageValidators().validate(_run_for("github_issue"))

    assert report.valid is True
    assert "has_goal_section" in report.passed_checks
    assert "has_review_or_oak" in report.passed_checks


def test_validator_reports_repair_quest_for_bad_markdown():
    run = LanguageRun(
        target_style="markdown_doc",
        audience="reviewer",
        draft="too short",
        clarity_score=0.2,
        safety_score=0.2,
        structure_score=0.1,
        oak_notes=[],
        m_plus=[],
        m_minus=[],
        next_quest="repair",
    )
    report = LanguageValidators().validate(run)

    assert report.valid is False
    assert report.failed_checks
    assert report.next_repair_quest.startswith("repair_")


def test_validation_report_rejects_out_of_range_score():
    try:
        ValidationReport(
            format_name="x",
            valid=False,
            score=2.0,
            checks=[ValidationCheck("check", False, "detail")],
            m_plus=[],
            m_minus=[],
            next_repair_quest="repair",
        )
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError("ValidationReport accepted out-of-range score")


def test_validate_many_preserves_count():
    runs = [_run_for("markdown_doc"), _run_for("json_contract")]
    reports = LanguageValidators().validate_many(runs)

    assert len(reports) == 2
    assert all(0.0 <= report.score <= 1.0 for report in reports)
