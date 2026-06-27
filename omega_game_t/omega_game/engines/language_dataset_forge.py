"""LanguageDatasetForge-T.

Build small internal benchmark datasets from the language stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .language_curriculum import CurriculumQuest, LanguageCurriculum
from .language_gm_rubric import LanguageGMEvaluation, LanguageGMRubric
from .language_repair_loop import LanguageRepairLoop, RepairLoopResult
from .language_validators import LanguageValidators, ValidationReport
from .polyglot_language import LanguageRun, PolyglotLanguageEngine


@dataclass(slots=True)
class LanguageDatasetItem:
    item_id: str
    quest: CurriculumQuest
    run: LanguageRun
    evaluation: LanguageGMEvaluation
    validation: ValidationReport
    repair: RepairLoopResult
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("LanguageDatasetItem.item_id must be non-empty.")

    @property
    def score_summary(self) -> dict[str, float | bool]:
        return {
            "run_score": self.run.score,
            "evaluation_score": self.evaluation.score,
            "validation_score": self.validation.score,
            "repair_score": self.repair.final_report.score,
            "repair_converged": self.repair.converged,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "quest": self.quest.to_dict(),
            "run": self.run.to_dict(),
            "evaluation": self.evaluation.to_dict(),
            "validation": self.validation.to_dict(),
            "repair": self.repair.to_dict(),
            "tags": list(self.tags),
            "score_summary": self.score_summary,
        }


@dataclass(slots=True)
class LanguageDataset:
    name: str
    items: list[LanguageDatasetItem]
    m_plus: list[str]
    m_minus: list[str]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("LanguageDataset.name must be non-empty.")

    def summary(self) -> dict[str, object]:
        if not self.items:
            return {"name": self.name, "count": 0, "average_repair_score": 0.0, "converged": 0, "tracks": []}
        average = sum(item.repair.final_report.score for item in self.items) / len(self.items)
        return {
            "name": self.name,
            "count": len(self.items),
            "average_repair_score": round(average, 4),
            "converged": sum(1 for item in self.items if item.repair.converged),
            "tracks": sorted({item.quest.track for item in self.items}),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "items": [item.to_dict() for item in self.items],
            "summary": self.summary(),
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
        }


class LanguageDatasetForge:
    """Forge small deterministic datasets for LanguageGM checks."""

    def __init__(
        self,
        curriculum: LanguageCurriculum | None = None,
        engine: PolyglotLanguageEngine | None = None,
        rubric: LanguageGMRubric | None = None,
        validators: LanguageValidators | None = None,
        repair_loop: LanguageRepairLoop | None = None,
    ) -> None:
        self.curriculum = curriculum or LanguageCurriculum()
        self.engine = engine or PolyglotLanguageEngine()
        self.rubric = rubric or LanguageGMRubric()
        self.validators = validators or LanguageValidators()
        self.repair_loop = repair_loop or LanguageRepairLoop(self.validators)

    def forge_item(self, quest: CurriculumQuest, item_id: str | None = None, target_score: float = 0.80) -> LanguageDatasetItem:
        language_quest = quest.to_language_quest()
        run = self.engine.transform(language_quest)
        evaluation = self.rubric.evaluate(run, expected_intent=quest.intent)
        validation = self.validators.validate(run)
        repair = self.repair_loop.repair(run, target_score=target_score, max_attempts=3)
        return LanguageDatasetItem(
            item_id=item_id or quest.quest_id,
            quest=quest,
            run=run,
            evaluation=evaluation,
            validation=validation,
            repair=repair,
            tags=[quest.track, quest.level, run.target_style],
        )

    def forge(self, name: str = "language_stack_dataset", max_items: int = 9, target_score: float = 0.80) -> LanguageDataset:
        if max_items < 0:
            raise ValueError("max_items must be >= 0.")
        quests = self.curriculum.default_quests()[:max_items]
        items = [self.forge_item(quest, target_score=target_score) for quest in quests]
        return LanguageDataset(
            name=name,
            items=items,
            m_plus=self._m_plus(items),
            m_minus=self._m_minus(items),
        )

    @staticmethod
    def _m_plus(items: list[LanguageDatasetItem]) -> list[str]:
        plus = ["dataset_forged"]
        if items and all(item.repair.converged for item in items):
            plus.append("all_repairs_converged")
        if items:
            plus.append("tracks_sampled")
        return plus

    @staticmethod
    def _m_minus(items: list[LanguageDatasetItem]) -> list[str]:
        if not items:
            return ["empty_dataset"]
        not_converged = [item.item_id for item in items if not item.repair.converged]
        if not_converged:
            return ["some_items_need_more_repair", *not_converged[:5]]
        return ["avoid_dataset_staleness"]


def default_language_dataset_forge() -> LanguageDatasetForge:
    return LanguageDatasetForge()


__all__ = [
    "LanguageDataset",
    "LanguageDatasetForge",
    "LanguageDatasetItem",
    "default_language_dataset_forge",
]
