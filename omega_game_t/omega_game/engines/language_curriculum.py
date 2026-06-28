"""LanguageCurriculum-T.

Progressive internal curriculum for LanguageGM training.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .language_gm_rubric import LanguageGMEvaluation, LanguageGMRubric
from .polyglot_language import LanguageQuest, PolyglotLanguageEngine

LEVELS = ["apprentice", "builder", "verifier", "strategist", "master"]
TRACK_TO_TARGET_STYLE = {
    "fr_clear": "fr_clear",
    "en_clear": "en_clear",
    "teaching": "teaching",
    "markdown_doc": "markdown_doc",
    "json_contract": "json_contract",
    "yaml_plan": "yaml_plan",
    "github_issue": "github_issue",
    "pitch": "pitch",
    "ip_caution": "ip_caution",
}


@dataclass(slots=True)
class CurriculumTrack:
    name: str
    target_style: str
    description: str
    required_skills: list[str]

    def __post_init__(self) -> None:
        if self.name not in TRACK_TO_TARGET_STYLE:
            raise ValueError(f"Unsupported curriculum track: {self.name}")
        if self.target_style != TRACK_TO_TARGET_STYLE[self.name]:
            raise ValueError("CurriculumTrack.target_style must match the track mapping.")
        if not self.required_skills:
            raise ValueError("CurriculumTrack.required_skills must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CurriculumQuest:
    quest_id: str
    track: str
    level: str
    source_text: str
    audience: str
    intent: str
    pass_threshold: float = 0.75
    constraints: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.quest_id.strip():
            raise ValueError("CurriculumQuest.quest_id must be non-empty.")
        if self.track not in TRACK_TO_TARGET_STYLE:
            raise ValueError(f"Unsupported quest track: {self.track}")
        if self.level not in LEVELS:
            raise ValueError(f"Unsupported quest level: {self.level}")
        if not 0.0 <= self.pass_threshold <= 1.0:
            raise ValueError("CurriculumQuest.pass_threshold must be in [0, 1].")

    def to_language_quest(self) -> LanguageQuest:
        return LanguageQuest(
            source_text=self.source_text,
            source_language="mixed",
            target_style=TRACK_TO_TARGET_STYLE[self.track],
            audience=self.audience,
            intent=self.intent,
            constraints=list(self.constraints),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CurriculumProgress:
    quest: CurriculumQuest
    evaluation: LanguageGMEvaluation
    passed: bool
    xp: int
    level_hint: str
    m_plus: list[str]
    m_minus: list[str]
    next_quest_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "quest": self.quest.to_dict(),
            "evaluation": self.evaluation.to_dict(),
            "passed": self.passed,
            "xp": self.xp,
            "level_hint": self.level_hint,
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "next_quest_id": self.next_quest_id,
        }


class LanguageCurriculum:
    """Build and evaluate LanguageGM curriculum quests."""

    def __init__(self, engine: PolyglotLanguageEngine | None = None, rubric: LanguageGMRubric | None = None) -> None:
        self.engine = engine or PolyglotLanguageEngine()
        self.rubric = rubric or LanguageGMRubric()

    def tracks(self) -> list[CurriculumTrack]:
        return [
            CurriculumTrack("fr_clear", "fr_clear", "Clear French explanations.", ["clarity", "nuance", "limits"]),
            CurriculumTrack("en_clear", "en_clear", "Clear English explanations.", ["plain_language", "structure"]),
            CurriculumTrack("teaching", "teaching", "Progressive teaching drafts.", ["examples", "audience_fit"]),
            CurriculumTrack("markdown_doc", "markdown_doc", "README and docs sections.", ["headings", "examples", "tests"]),
            CurriculumTrack("json_contract", "json_contract", "Structured JSON contracts.", ["schema", "required_fields"]),
            CurriculumTrack("yaml_plan", "yaml_plan", "Readable plans and manifests.", ["plan_shape", "constraints"]),
            CurriculumTrack("github_issue", "github_issue", "Issue and review-path writing.", ["goal", "tasks", "checks"]),
            CurriculumTrack("pitch", "pitch", "Cautious value framing.", ["audience", "evidence", "ask"]),
            CurriculumTrack("ip_caution", "ip_caution", "Review-sensitive caution notes.", ["boundaries", "review_status"]),
        ]

    def quests_for_track(self, track: str) -> list[CurriculumQuest]:
        if track not in TRACK_TO_TARGET_STYLE:
            raise ValueError(f"Unsupported track: {track}")
        return [
            CurriculumQuest(
                quest_id=f"{track}-apprentice-01",
                track=track,
                level="apprentice",
                source_text="Explain this Omega GAME T module in a simple way.",
                audience="new contributor",
                intent="make the idea understandable and bounded",
                pass_threshold=0.60,
                constraints=["plain language", "limits visible"],
            ),
            CurriculumQuest(
                quest_id=f"{track}-builder-01",
                track=track,
                level="builder",
                source_text="Turn this module idea into a reviewable repo artifact.",
                audience="repo reviewer",
                intent="produce a structured draft with checks",
                pass_threshold=0.72,
                constraints=["include checks", "state assumptions"],
            ),
            CurriculumQuest(
                quest_id=f"{track}-verifier-01",
                track=track,
                level="verifier",
                source_text="Review and improve the draft for hidden claims and format drift.",
                audience="maintainer",
                intent="reduce ambiguity and preserve OAK notes",
                pass_threshold=0.80,
                constraints=["avoid hidden claims", "preserve intent"],
            ),
        ]

    def default_quests(self) -> list[CurriculumQuest]:
        quests: list[CurriculumQuest] = []
        for track in TRACK_TO_TARGET_STYLE:
            quests.extend(self.quests_for_track(track))
        return quests

    def run_quest(self, quest: CurriculumQuest) -> CurriculumProgress:
        language_quest = quest.to_language_quest()
        run = self.engine.transform(language_quest)
        evaluation = self.rubric.evaluate(run, expected_intent=quest.intent)
        passed = evaluation.score >= quest.pass_threshold
        return CurriculumProgress(
            quest=quest,
            evaluation=evaluation,
            passed=passed,
            xp=self._xp_for(evaluation, passed),
            level_hint=self._level_hint(quest, evaluation.score),
            m_plus=list(dict.fromkeys(evaluation.m_plus + (["quest_passed"] if passed else []))),
            m_minus=list(dict.fromkeys(evaluation.m_minus + ([] if passed else ["repeat_or_simplify_quest"]))),
            next_quest_id=self.next_quest_id(quest, evaluation),
        )

    def evaluate_progress(self, progress_items: list[CurriculumProgress]) -> dict[str, object]:
        if not progress_items:
            return {"count": 0, "average_score": 0.0, "passed": 0, "xp": 0, "level_hint": "apprentice"}
        average = sum(item.evaluation.score for item in progress_items) / len(progress_items)
        passed = sum(1 for item in progress_items if item.passed)
        xp = sum(item.xp for item in progress_items)
        return {
            "count": len(progress_items),
            "average_score": round(average, 4),
            "passed": passed,
            "xp": xp,
            "level_hint": self._global_level_hint(average),
        }

    def next_quest_id(self, quest: CurriculumQuest, evaluation: LanguageGMEvaluation) -> str:
        if evaluation.score < quest.pass_threshold:
            return quest.quest_id
        level_index = LEVELS.index(quest.level)
        next_level = LEVELS[min(level_index + 1, len(LEVELS) - 1)]
        return f"{quest.track}-{next_level}-01"

    @staticmethod
    def _xp_for(evaluation: LanguageGMEvaluation, passed: bool) -> int:
        base = int(round(evaluation.score * 100))
        return base + (20 if passed else 0)

    @staticmethod
    def _level_hint(quest: CurriculumQuest, score: float) -> str:
        if score < quest.pass_threshold:
            return quest.level
        index = LEVELS.index(quest.level)
        return LEVELS[min(index + 1, len(LEVELS) - 1)]

    @staticmethod
    def _global_level_hint(average_score: float) -> str:
        if average_score >= 0.90:
            return "master"
        if average_score >= 0.80:
            return "strategist"
        if average_score >= 0.65:
            return "builder"
        if average_score >= 0.50:
            return "apprentice"
        return "needs_practice"


def default_language_curriculum() -> LanguageCurriculum:
    return LanguageCurriculum()


__all__ = [
    "CurriculumProgress",
    "CurriculumQuest",
    "CurriculumTrack",
    "LanguageCurriculum",
    "default_language_curriculum",
]
