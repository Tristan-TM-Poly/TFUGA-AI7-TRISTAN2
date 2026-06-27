"""LanguageValidators-T.

Lightweight structural validators for LanguageRun outputs.
These checks are internal training signals, not official certification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .polyglot_language import LanguageRun


@dataclass(slots=True)
class ValidationCheck:
    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ValidationCheck.name must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ValidationReport:
    format_name: str
    valid: bool
    score: float
    checks: list[ValidationCheck]
    m_plus: list[str]
    m_minus: list[str]
    next_repair_quest: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("ValidationReport.score must be in [0, 1].")
        if not self.checks:
            raise ValueError("ValidationReport.checks must be non-empty.")

    @property
    def passed_checks(self) -> list[str]:
        return [check.name for check in self.checks if check.passed]

    @property
    def failed_checks(self) -> list[str]:
        return [check.name for check in self.checks if not check.passed]

    def to_dict(self) -> dict[str, object]:
        return {
            "format_name": self.format_name,
            "valid": self.valid,
            "score": self.score,
            "checks": [check.to_dict() for check in self.checks],
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "next_repair_quest": self.next_repair_quest,
        }


class LanguageValidators:
    """Validate draft structure for selected LanguageRun target styles."""

    def validate(self, run: LanguageRun) -> ValidationReport:
        draft = run.draft.strip()
        if run.target_style == "markdown_doc":
            checks = self._markdown_checks(draft)
        elif run.target_style == "json_contract":
            checks = self._json_contract_checks(draft)
        elif run.target_style == "yaml_plan":
            checks = self._yaml_plan_checks(draft)
        elif run.target_style == "github_issue":
            checks = self._github_issue_checks(draft)
        else:
            checks = self._generic_checks(draft)
        return self._report(run.target_style, checks)

    def validate_many(self, runs: list[LanguageRun]) -> list[ValidationReport]:
        return [self.validate(run) for run in runs]

    @staticmethod
    def _markdown_checks(draft: str) -> list[ValidationCheck]:
        lower = draft.lower()
        return [
            ValidationCheck("has_title_heading", draft.startswith("# "), "Markdown docs should start with a level-1 title."),
            ValidationCheck("has_section_heading", "\n## " in draft, "Markdown docs should contain section headings."),
            ValidationCheck("has_oak_or_boundary", "oak" in lower or "boundary" in lower or "limits" in lower, "OAK or boundary notes should be visible."),
            ValidationCheck("has_body_content", len(draft.split()) >= 20, "Draft should contain enough body content to review."),
        ]

    @staticmethod
    def _json_contract_checks(draft: str) -> list[ValidationCheck]:
        lower = draft.lower()
        return [
            ValidationCheck("looks_like_object", draft.startswith("{") and draft.endswith("}"), "JSON contract should look like an object."),
            ValidationCheck("has_intent", "intent" in lower, "JSON contract should expose intent."),
            ValidationCheck("has_audience", "audience" in lower, "JSON contract should expose audience."),
            ValidationCheck("has_status", "status" in lower, "JSON contract should expose status."),
            ValidationCheck("has_oak", "oak" in lower or "limits" in lower, "JSON contract should expose OAK or limits."),
        ]

    @staticmethod
    def _yaml_plan_checks(draft: str) -> list[ValidationCheck]:
        lower = draft.lower()
        lines = [line for line in draft.splitlines() if line.strip()]
        return [
            ValidationCheck("has_key_value_lines", sum(1 for line in lines if ":" in line) >= 3, "YAML plan should contain several key-value lines."),
            ValidationCheck("has_intent_or_goal", "intent:" in lower or "goal:" in lower, "YAML plan should expose intent or goal."),
            ValidationCheck("has_status", "status:" in lower, "YAML plan should expose status."),
            ValidationCheck("has_oak_or_constraints", "oak:" in lower or "constraints:" in lower, "YAML plan should expose OAK or constraints."),
        ]

    @staticmethod
    def _github_issue_checks(draft: str) -> list[ValidationCheck]:
        lower = draft.lower()
        return [
            ValidationCheck("has_goal_section", "## goal" in lower or "# goal" in lower, "Issue draft should include a goal section."),
            ValidationCheck("has_context_or_notes", "## notes" in lower or "## context" in lower, "Issue draft should include notes or context."),
            ValidationCheck("has_review_or_oak", "oak" in lower or "review" in lower or "checks" in lower, "Issue draft should include OAK, review, or checks."),
            ValidationCheck("has_body_content", len(draft.split()) >= 18, "Issue draft should contain enough body content."),
        ]

    @staticmethod
    def _generic_checks(draft: str) -> list[ValidationCheck]:
        lower = draft.lower()
        return [
            ValidationCheck("has_text", bool(draft), "Draft should not be empty."),
            ValidationCheck("has_enough_words", len(draft.split()) >= 8, "Draft should contain enough words to review."),
            ValidationCheck("has_limits_or_review_note", "limit" in lower or "review" in lower or "oak" in lower, "Draft should expose limits, review, or OAK notes."),
        ]

    @staticmethod
    def _report(format_name: str, checks: list[ValidationCheck]) -> ValidationReport:
        passed = sum(1 for check in checks if check.passed)
        score = round(passed / len(checks), 4)
        valid = score >= 0.80
        failed = [check.name for check in checks if not check.passed]
        return ValidationReport(
            format_name=format_name,
            valid=valid,
            score=score,
            checks=checks,
            m_plus=["structure_validated", f"{format_name}_checks_ran"] if valid else ["validation_attempt_recorded"],
            m_minus=[f"fix_{name}" for name in failed] if failed else ["avoid_format_regression"],
            next_repair_quest="none" if valid else f"repair_{failed[0]}",
        )


def default_language_validators() -> LanguageValidators:
    return LanguageValidators()


__all__ = [
    "LanguageValidators",
    "ValidationCheck",
    "ValidationReport",
    "default_language_validators",
]
