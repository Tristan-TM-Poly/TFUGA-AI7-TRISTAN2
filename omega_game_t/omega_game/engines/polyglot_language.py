"""PolyglotLanguageEngine-T.

Small OAK-safe split unit for language and technical-writing quests.
It creates internal drafts only; it is not official translation, legal advice,
patent advice, or external certification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

SUPPORTED_TARGETS = {
    "fr_clear",
    "en_clear",
    "teaching",
    "pitch",
    "markdown_doc",
    "json_contract",
    "yaml_plan",
    "github_issue",
    "ip_caution",
}

SENSITIVE_TARGETS = {"pitch", "github_issue", "ip_caution"}


@dataclass(slots=True)
class LanguageQuest:
    """A language transformation quest for a GameMaster."""

    source_text: str
    source_language: str
    target_style: str
    audience: str
    intent: str
    constraints: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source_text.strip():
            raise ValueError("LanguageQuest.source_text must be non-empty.")
        if self.target_style not in SUPPORTED_TARGETS:
            raise ValueError(f"Unsupported target_style: {self.target_style}")
        if not self.audience.strip():
            raise ValueError("LanguageQuest.audience must be non-empty.")
        if not self.intent.strip():
            raise ValueError("LanguageQuest.intent must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class LanguageRun:
    """Result of a PolyglotLanguageEngine quest."""

    target_style: str
    audience: str
    draft: str
    clarity_score: float
    safety_score: float
    structure_score: float
    oak_notes: list[str]
    m_plus: list[str]
    m_minus: list[str]
    next_quest: str

    def __post_init__(self) -> None:
        for key in ("clarity_score", "safety_score", "structure_score"):
            value = getattr(self, key)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{key} must be in [0, 1].")

    @property
    def score(self) -> float:
        return round(0.40 * self.clarity_score + 0.35 * self.safety_score + 0.25 * self.structure_score, 4)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["score"] = self.score
        return payload


class PolyglotLanguageEngine:
    """Transform rough ideas into OAK-safe language drafts."""

    name = "PolyglotLanguageEngine-T"

    def transform(self, quest: LanguageQuest) -> LanguageRun:
        draft = self._draft_for(quest)
        oak_notes = self._oak_notes(quest)
        clarity = self._clarity_score(quest, draft)
        safety = self._safety_score(quest, oak_notes)
        structure = self._structure_score(quest, draft)
        return LanguageRun(
            target_style=quest.target_style,
            audience=quest.audience,
            draft=draft,
            clarity_score=clarity,
            safety_score=safety,
            structure_score=structure,
            oak_notes=oak_notes,
            m_plus=self._m_plus(quest),
            m_minus=self._m_minus(quest),
            next_quest=self._next_quest(quest),
        )

    def default_quests(self) -> list[LanguageQuest]:
        return [
            LanguageQuest(
                source_text="Transform my prototype into a clear explanation.",
                source_language="en",
                target_style="teaching",
                audience="new builder",
                intent="explain value and limits",
                constraints=["plain language", "limits visible"],
            ),
            LanguageQuest(
                source_text="Turn this module into GitHub documentation.",
                source_language="en",
                target_style="markdown_doc",
                audience="repo reviewer",
                intent="document behavior and tests",
                constraints=["include OAK notes"],
            ),
            LanguageQuest(
                source_text="Prepare a cautious invention note.",
                source_language="en",
                target_style="ip_caution",
                audience="internal reviewer",
                intent="protect uncertainty and review status",
                constraints=["no public disclosure claim", "review required"],
            ),
        ]

    def _draft_for(self, quest: LanguageQuest) -> str:
        prefix = f"Intent: {quest.intent}. Audience: {quest.audience}."
        if quest.target_style == "json_contract":
            return (
                '{\n'
                f'  "intent": "{quest.intent}",\n'
                f'  "audience": "{quest.audience}",\n'
                '  "status": "draft",\n'
                '  "oak": "limits_visible"\n'
                '}'
            )
        if quest.target_style == "yaml_plan":
            return (
                f"intent: {quest.intent}\n"
                f"audience: {quest.audience}\n"
                "status: draft\n"
                "oak: limits_visible\n"
            )
        if quest.target_style == "markdown_doc":
            return f"# Draft\n\n{prefix}\n\n## Source\n\n{quest.source_text}\n\n## OAK\n\nLimits and assumptions must stay visible."
        if quest.target_style == "github_issue":
            return f"## Goal\n\n{quest.intent}\n\n## Audience\n\n{quest.audience}\n\n## Notes\n\n{quest.source_text}\n\n## OAK\n\nReview before external use."
        if quest.target_style == "pitch":
            return f"{quest.source_text.strip()} — framed for {quest.audience}, with clear limits and a review step."
        if quest.target_style == "ip_caution":
            return f"Internal caution note: {quest.source_text.strip()} Review status, novelty, public disclosure risk, and claims must be checked before external sharing."
        if quest.target_style == "fr_clear":
            return f"Version claire en francais: {quest.source_text.strip()} Limites: hypothese interne a revoir."
        if quest.target_style == "en_clear":
            return f"Clear English version: {quest.source_text.strip()} Limits: internal draft to review."
        return f"Teaching draft: {prefix} Core idea: {quest.source_text.strip()} Limits and examples should be explicit."

    def _oak_notes(self, quest: LanguageQuest) -> list[str]:
        notes = ["preserve_intent", "limits_visible", "audience_named"]
        if quest.target_style in SENSITIVE_TARGETS:
            notes.append("human_review_before_external_use")
        if "ip" in quest.target_style or any("review" in item for item in quest.constraints):
            notes.append("ip_or_claims_review_required")
        return list(dict.fromkeys(notes))

    @staticmethod
    def _clarity_score(quest: LanguageQuest, draft: str) -> float:
        base = 0.60
        if quest.audience:
            base += 0.10
        if quest.intent:
            base += 0.10
        if len(draft) >= 80:
            base += 0.05
        return min(1.0, base)

    @staticmethod
    def _safety_score(quest: LanguageQuest, oak_notes: list[str]) -> float:
        base = 0.70
        if "limits_visible" in oak_notes:
            base += 0.10
        if quest.target_style in SENSITIVE_TARGETS and "human_review_before_external_use" in oak_notes:
            base += 0.10
        if any("no public" in item.lower() or "review" in item.lower() for item in quest.constraints):
            base += 0.05
        return min(1.0, base)

    @staticmethod
    def _structure_score(quest: LanguageQuest, draft: str) -> float:
        if quest.target_style in {"json_contract", "yaml_plan", "markdown_doc", "github_issue"}:
            return 0.90
        if len(draft.split()) >= 12:
            return 0.78
        return 0.65

    @staticmethod
    def _m_plus(quest: LanguageQuest) -> list[str]:
        return [f"{quest.target_style}_draft_created", "intent_preserved", "audience_named"]

    @staticmethod
    def _m_minus(quest: LanguageQuest) -> list[str]:
        minus = ["avoid_false_authority", "avoid_hidden_claims"]
        if quest.target_style in SENSITIVE_TARGETS:
            minus.append("external_use_requires_review")
        return minus

    @staticmethod
    def _next_quest(quest: LanguageQuest) -> str:
        if quest.target_style in {"json_contract", "yaml_plan"}:
            return "validate_structure_against_schema"
        if quest.target_style == "markdown_doc":
            return "add_examples_and_tests_section"
        if quest.target_style in SENSITIVE_TARGETS:
            return "run_claims_and_review_pass"
        return "create_second_audience_variant"


def default_polyglot_language_engine() -> PolyglotLanguageEngine:
    return PolyglotLanguageEngine()


__all__ = ["LanguageQuest", "LanguageRun", "PolyglotLanguageEngine", "default_polyglot_language_engine"]
