"""LanguageRepairLoop-T.

Deterministic internal repair loop for LanguageRun drafts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .language_validators import LanguageValidators, ValidationReport
from .polyglot_language import LanguageRun


@dataclass(slots=True)
class RepairAction:
    check_name: str
    instruction: str
    applied: bool = True

    def __post_init__(self) -> None:
        if not self.check_name.strip():
            raise ValueError("RepairAction.check_name must be non-empty.")
        if not self.instruction.strip():
            raise ValueError("RepairAction.instruction must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RepairAttempt:
    index: int
    before_score: float
    after_score: float
    actions: list[RepairAction]
    report_after: ValidationReport

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("RepairAttempt.index must be >= 1.")
        if not 0.0 <= self.before_score <= 1.0:
            raise ValueError("RepairAttempt.before_score must be in [0, 1].")
        if not 0.0 <= self.after_score <= 1.0:
            raise ValueError("RepairAttempt.after_score must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "before_score": self.before_score,
            "after_score": self.after_score,
            "actions": [action.to_dict() for action in self.actions],
            "report_after": self.report_after.to_dict(),
        }


@dataclass(slots=True)
class RepairLoopResult:
    target_score: float
    converged: bool
    final_run: LanguageRun
    final_report: ValidationReport
    attempts: list[RepairAttempt]
    m_plus: list[str]
    m_minus: list[str]
    next_action: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.target_score <= 1.0:
            raise ValueError("RepairLoopResult.target_score must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        return {
            "target_score": self.target_score,
            "converged": self.converged,
            "final_run": self.final_run.to_dict(),
            "final_report": self.final_report.to_dict(),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "next_action": self.next_action,
        }


class LanguageRepairLoop:
    """Repair LanguageRun drafts using validator feedback."""

    def __init__(self, validators: LanguageValidators | None = None) -> None:
        self.validators = validators or LanguageValidators()

    def repair(self, run: LanguageRun, target_score: float = 0.80, max_attempts: int = 3) -> RepairLoopResult:
        if not 0.0 <= target_score <= 1.0:
            raise ValueError("target_score must be in [0, 1].")
        if max_attempts < 0:
            raise ValueError("max_attempts must be >= 0.")
        current_run = run
        report = self.validators.validate(current_run)
        attempts: list[RepairAttempt] = []
        for index in range(1, max_attempts + 1):
            if report.score >= target_score:
                break
            before_score = report.score
            current_run, actions = self._apply_repairs(current_run, report)
            report = self.validators.validate(current_run)
            attempts.append(
                RepairAttempt(
                    index=index,
                    before_score=before_score,
                    after_score=report.score,
                    actions=actions,
                    report_after=report,
                )
            )
        converged = report.score >= target_score
        return RepairLoopResult(
            target_score=target_score,
            converged=converged,
            final_run=current_run,
            final_report=report,
            attempts=attempts,
            m_plus=self._m_plus(converged, report),
            m_minus=self._m_minus(converged, report),
            next_action="none" if converged else report.next_repair_quest,
        )

    def _apply_repairs(self, run: LanguageRun, report: ValidationReport) -> tuple[LanguageRun, list[RepairAction]]:
        draft = run.draft
        actions: list[RepairAction] = []
        for check_name in report.failed_checks:
            draft, instruction = self._repair_check(run.target_style, draft, check_name)
            actions.append(RepairAction(check_name=check_name, instruction=instruction))
        repaired = LanguageRun(
            target_style=run.target_style,
            audience=run.audience,
            draft=draft,
            clarity_score=min(1.0, run.clarity_score + 0.10),
            safety_score=min(1.0, run.safety_score + 0.10),
            structure_score=min(1.0, run.structure_score + 0.15),
            oak_notes=list(dict.fromkeys(run.oak_notes + ["repair_loop_applied", "limits_visible"])),
            m_plus=list(dict.fromkeys(run.m_plus + ["draft_repaired"])),
            m_minus=list(dict.fromkeys(run.m_minus + ["repair_loop_required"])),
            next_quest="revalidate_repaired_draft",
        )
        return repaired, actions

    def _repair_check(self, target_style: str, draft: str, check_name: str) -> tuple[str, str]:
        if target_style == "markdown_doc":
            return self._repair_markdown(draft, check_name)
        if target_style == "json_contract":
            return self._repair_json(draft, check_name)
        if target_style == "yaml_plan":
            return self._repair_yaml(draft, check_name)
        if target_style == "github_issue":
            return self._repair_issue(draft, check_name)
        return self._repair_generic(draft, check_name)

    @staticmethod
    def _repair_markdown(draft: str, check_name: str) -> tuple[str, str]:
        if check_name == "has_title_heading":
            return f"# Draft\n\n{draft.strip()}", "Add level-1 Markdown title."
        if check_name == "has_section_heading":
            return f"{draft.rstrip()}\n\n## Notes\n\nStructure added for review.", "Add Markdown section heading."
        if check_name == "has_oak_or_boundary":
            return f"{draft.rstrip()}\n\n## OAK\n\nLimits and assumptions remain visible for review.", "Add OAK section."
        if check_name == "has_body_content":
            return f"{draft.rstrip()}\n\nThis draft now includes enough context for review, including purpose, checks, assumptions, and next steps.", "Add body content."
        return f"{draft.rstrip()}\n\nRepair note: {check_name}.", "Add generic Markdown repair note."

    @staticmethod
    def _repair_json(draft: str, check_name: str) -> tuple[str, str]:
        repaired = (
            '{\n'
            '  "intent": "repair draft structure",\n'
            '  "audience": "reviewer",\n'
            '  "status": "draft",\n'
            '  "oak": "limits_visible"\n'
            '}'
        )
        return repaired, f"Replace with minimal JSON contract covering {check_name}."

    @staticmethod
    def _repair_yaml(draft: str, check_name: str) -> tuple[str, str]:
        repaired = (
            "intent: repair draft structure\n"
            "audience: reviewer\n"
            "status: draft\n"
            "oak: limits_visible\n"
        )
        return repaired, f"Replace with minimal YAML plan covering {check_name}."

    @staticmethod
    def _repair_issue(draft: str, check_name: str) -> tuple[str, str]:
        repaired = (
            "## Goal\n\nRepair draft structure.\n\n"
            "## Notes\n\nThe draft needs clear context and reviewable checks.\n\n"
            "## OAK\n\nReview notes and limits remain visible."
        )
        return repaired, f"Replace with minimal issue draft covering {check_name}."

    @staticmethod
    def _repair_generic(draft: str, check_name: str) -> tuple[str, str]:
        if check_name == "has_text":
            return "Draft repaired for review.", "Add non-empty text."
        if check_name == "has_enough_words":
            return f"{draft.rstrip()} This draft now includes enough words for basic review and improvement.", "Add words."
        if check_name == "has_limits_or_review_note":
            return f"{draft.rstrip()} Review note: limits and assumptions should remain visible.", "Add review note."
        return f"{draft.rstrip()} Repair note: {check_name}.", "Add generic repair note."

    @staticmethod
    def _m_plus(converged: bool, report: ValidationReport) -> list[str]:
        if converged:
            return ["repair_loop_converged", "validation_target_reached", *report.m_plus]
        return ["repair_loop_attempted"]

    @staticmethod
    def _m_minus(converged: bool, report: ValidationReport) -> list[str]:
        if converged:
            return ["avoid_future_format_regression"]
        return ["repair_loop_not_converged", *report.m_minus]


def default_language_repair_loop() -> LanguageRepairLoop:
    return LanguageRepairLoop()


__all__ = [
    "LanguageRepairLoop",
    "RepairAction",
    "RepairAttempt",
    "RepairLoopResult",
    "default_language_repair_loop",
]
