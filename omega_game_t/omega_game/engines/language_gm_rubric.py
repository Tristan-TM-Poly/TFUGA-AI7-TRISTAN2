"""LanguageGM Rubric-T.

Internal evaluation layer for PolyglotLanguageEngine-T outputs.
It is a training signal, not an official language certification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .polyglot_language import LanguageRun


@dataclass(slots=True)
class LanguageRubricScores:
    clarity: float
    structure: float
    audience_fit: float
    format_fit: float
    oak_safety: float
    intent_preservation: float
    drift: float = 0.0
    hidden_claims: float = 0.0

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{key} must be in [0, 1].")

    def score(self) -> float:
        positive = (
            0.18 * self.clarity
            + 0.16 * self.structure
            + 0.14 * self.audience_fit
            + 0.14 * self.format_fit
            + 0.20 * self.oak_safety
            + 0.18 * self.intent_preservation
        )
        penalty = 0.12 * self.drift + 0.12 * self.hidden_claims
        return max(0.0, min(1.0, positive - penalty))

    def level(self) -> str:
        score = self.score()
        if score >= 0.90:
            return "master"
        if score >= 0.80:
            return "strategist"
        if score >= 0.65:
            return "builder"
        if score >= 0.50:
            return "apprentice"
        return "needs_practice"

    def to_dict(self) -> dict[str, float | str]:
        payload = asdict(self)
        payload["score"] = self.score()
        payload["level"] = self.level()
        return payload


@dataclass(slots=True)
class LanguageGMEvaluation:
    target_style: str
    audience: str
    scores: LanguageRubricScores
    m_plus: list[str]
    m_minus: list[str]
    next_training_quest: str

    @property
    def score(self) -> float:
        return self.scores.score()

    @property
    def level(self) -> str:
        return self.scores.level()

    def to_dict(self) -> dict[str, object]:
        return {
            "target_style": self.target_style,
            "audience": self.audience,
            "score": self.score,
            "level": self.level,
            "scores": self.scores.to_dict(),
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "next_training_quest": self.next_training_quest,
        }


class LanguageGMRubric:
    """Evaluate LanguageRun outputs as internal GameMaster training signals."""

    def evaluate(self, run: LanguageRun, expected_intent: str | None = None) -> LanguageGMEvaluation:
        scores = self._scores_for(run, expected_intent)
        return LanguageGMEvaluation(
            target_style=run.target_style,
            audience=run.audience,
            scores=scores,
            m_plus=self._m_plus(run, scores),
            m_minus=self._m_minus(run, scores),
            next_training_quest=self._next_training_quest(run, scores),
        )

    def evaluate_many(self, runs: list[LanguageRun]) -> list[LanguageGMEvaluation]:
        return [self.evaluate(run) for run in runs]

    def _scores_for(self, run: LanguageRun, expected_intent: str | None) -> LanguageRubricScores:
        draft = run.draft.strip()
        format_fit = self._format_fit(run.target_style, draft)
        oak_safety = min(1.0, run.safety_score + (0.05 if "limits_visible" in run.oak_notes else 0.0))
        intent_preservation = 0.78 if not expected_intent else (0.88 if expected_intent.lower()[:12] in draft.lower() else 0.70)
        hidden_claims = 0.20 if any(word in draft.lower() for word in ["guaranteed", "officially proven", "certain profit"]) else 0.02
        drift = 0.05 if run.audience and run.target_style else 0.20
        return LanguageRubricScores(
            clarity=run.clarity_score,
            structure=run.structure_score,
            audience_fit=0.85 if run.audience else 0.45,
            format_fit=format_fit,
            oak_safety=oak_safety,
            intent_preservation=intent_preservation,
            drift=drift,
            hidden_claims=hidden_claims,
        )

    @staticmethod
    def _format_fit(target_style: str, draft: str) -> float:
        if target_style == "markdown_doc":
            return 0.90 if draft.startswith("#") and "##" in draft else 0.55
        if target_style == "json_contract":
            return 0.90 if draft.startswith("{") and draft.endswith("}") else 0.45
        if target_style == "yaml_plan":
            return 0.90 if ":" in draft and "status:" in draft else 0.50
        if target_style == "github_issue":
            return 0.88 if "##" in draft and "Goal" in draft else 0.55
        return 0.78 if len(draft.split()) >= 8 else 0.55

    @staticmethod
    def _m_plus(run: LanguageRun, scores: LanguageRubricScores) -> list[str]:
        plus = []
        if scores.clarity >= 0.75:
            plus.append("clear_output")
        if scores.format_fit >= 0.80:
            plus.append(f"{run.target_style}_format_fit")
        if scores.oak_safety >= 0.85:
            plus.append("oak_notes_visible")
        if scores.intent_preservation >= 0.75:
            plus.append("intent_preserved")
        return plus or ["language_run_completed"]

    @staticmethod
    def _m_minus(run: LanguageRun, scores: LanguageRubricScores) -> list[str]:
        minus = []
        if scores.clarity < 0.65:
            minus.append("clarity_needs_practice")
        if scores.format_fit < 0.65:
            minus.append(f"{run.target_style}_format_needs_practice")
        if scores.hidden_claims > 0.10:
            minus.append("hidden_claims_detected")
        if scores.oak_safety < 0.75:
            minus.append("oak_notes_need_strengthening")
        return minus or ["avoid_overconfidence"]

    @staticmethod
    def _next_training_quest(run: LanguageRun, scores: LanguageRubricScores) -> str:
        if scores.format_fit < 0.65:
            return f"practice_{run.target_style}_format"
        if scores.oak_safety < 0.75:
            return "add_limits_and_review_notes"
        if scores.clarity < 0.65:
            return "rewrite_for_plain_language"
        if scores.score() >= 0.80:
            return "create_second_audience_variant"
        return "repeat_with_tighter_intent"


def default_language_gm_rubric() -> LanguageGMRubric:
    return LanguageGMRubric()


__all__ = [
    "LanguageGMEvaluation",
    "LanguageGMRubric",
    "LanguageRubricScores",
    "default_language_gm_rubric",
]
