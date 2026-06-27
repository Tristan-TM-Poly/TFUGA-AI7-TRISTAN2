"""GameMasterAcademy-T.

Internal training and evaluation system for specialized GameMasters.
It does not grant external credentials or perform external actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


LEVELS = ["apprentice", "builder", "verifier", "strategist", "master"]
CORE_SKILLS = ["observe", "explain", "simulate", "test", "document", "oak_check", "memory_update", "next_quest"]


@dataclass(slots=True)
class SkillScore:
    name: str
    score: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("SkillScore.name must be non-empty.")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("SkillScore.score must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class GameMasterProfile:
    name: str
    domain: str
    level: str
    skills: list[SkillScore]
    oak_rules: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.level not in LEVELS:
            raise ValueError("GameMasterProfile.level must be a supported level.")
        if not self.skills:
            raise ValueError("GameMasterProfile.skills must be non-empty.")

    def average_skill(self) -> float:
        return sum(skill.score for skill in self.skills) / len(self.skills)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "domain": self.domain,
            "level": self.level,
            "average_skill": self.average_skill(),
            "skills": [skill.to_dict() for skill in self.skills],
            "oak_rules": list(self.oak_rules),
        }


@dataclass(slots=True)
class TrainingQuest:
    name: str
    domain: str
    target_skill: str
    difficulty: float
    prompt: str
    oak_checks: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("TrainingQuest.name must be non-empty.")
        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError("TrainingQuest.difficulty must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class EvaluationRubric:
    domain_skill: float
    reasoning: float
    safety: float
    clarity: float
    memory: float
    overclaim: float = 0.0
    drift: float = 0.0

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{key} must be in [0, 1].")

    def score(self) -> float:
        positive = (
            0.24 * self.domain_skill
            + 0.20 * self.reasoning
            + 0.22 * self.safety
            + 0.18 * self.clarity
            + 0.16 * self.memory
        )
        penalty = 0.12 * self.overclaim + 0.08 * self.drift
        return max(0.0, min(1.0, positive - penalty))

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["score"] = self.score()
        return payload


@dataclass(slots=True)
class AcademyEvaluation:
    profile: GameMasterProfile
    quest: TrainingQuest
    rubric: EvaluationRubric
    passed: bool
    next_level_hint: str
    m_plus: list[str]
    m_minus: list[str]
    next_quests: list[TrainingQuest]

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile.to_dict(),
            "quest": self.quest.to_dict(),
            "rubric": self.rubric.to_dict(),
            "passed": self.passed,
            "next_level_hint": self.next_level_hint,
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "next_quests": [quest.to_dict() for quest in self.next_quests],
        }


class GameMasterAcademy:
    """Create and evaluate internal GameMaster training paths."""

    def default_profiles(self) -> list[GameMasterProfile]:
        return [
            self.profile("RepoGM", "repo", "builder"),
            self.profile("CodeGM", "code", "builder"),
            self.profile("EnergyGM", "energy", "apprentice"),
            self.profile("ProcessGM", "process", "apprentice"),
            self.profile("RevenueGM", "revenue", "builder"),
            self.profile("LanguageGM", "language", "builder"),
        ]

    def profile(self, name: str, domain: str, level: str = "apprentice") -> GameMasterProfile:
        base = 0.55 + LEVELS.index(level) * 0.08
        skills = [SkillScore(skill, min(1.0, base + (0.05 if skill in {"oak_check", "memory_update"} else 0.0))) for skill in CORE_SKILLS]
        return GameMasterProfile(
            name=name,
            domain=domain,
            level=level,
            skills=skills,
            oak_rules=[
                "limits_visible",
                "internal_evaluation_only",
                "no_external_authority_claim",
                "record_m_plus_and_m_minus",
            ],
        )

    def quests_for(self, domain: str) -> list[TrainingQuest]:
        return [
            TrainingQuest(
                name=f"{domain}_observe_world",
                domain=domain,
                target_skill="observe",
                difficulty=0.35,
                prompt=f"Map the current {domain} world into nodes, risks and next actions.",
                oak_checks=["limits_visible", "assumptions_listed"],
            ),
            TrainingQuest(
                name=f"{domain}_simulate_safe_action",
                domain=domain,
                target_skill="simulate",
                difficulty=0.55,
                prompt=f"Simulate one safe internal action for the {domain} world.",
                oak_checks=["simulation_only", "no_external_action"],
            ),
            TrainingQuest(
                name=f"{domain}_memory_update",
                domain=domain,
                target_skill="memory_update",
                difficulty=0.50,
                prompt=f"Extract M+ and M- from a {domain} training run.",
                oak_checks=["m_plus_recorded", "m_minus_recorded"],
            ),
        ]

    def evaluate(self, profile: GameMasterProfile, quest: TrainingQuest) -> AcademyEvaluation:
        domain_match = 1.0 if profile.domain == quest.domain else 0.55
        average = profile.average_skill()
        difficulty_factor = max(0.0, 1.0 - quest.difficulty * 0.35)
        rubric = EvaluationRubric(
            domain_skill=max(0.0, min(1.0, average * domain_match)),
            reasoning=max(0.0, min(1.0, average * difficulty_factor)),
            safety=self._skill(profile, "oak_check"),
            clarity=self._skill(profile, "explain"),
            memory=self._skill(profile, "memory_update"),
            overclaim=0.05 if "internal_evaluation_only" in profile.oak_rules else 0.20,
            drift=0.05 if profile.domain == quest.domain else 0.25,
        )
        score = rubric.score()
        passed = score >= 0.60
        return AcademyEvaluation(
            profile=profile,
            quest=quest,
            rubric=rubric,
            passed=passed,
            next_level_hint=self._next_level_hint(profile, score),
            m_plus=[f"{profile.name}_{quest.target_skill}_trained"] if passed else ["training_attempt_recorded"],
            m_minus=[] if passed else ["skill_gap_needs_practice"],
            next_quests=self.quests_for(profile.domain)[:2],
        )

    @staticmethod
    def _skill(profile: GameMasterProfile, skill_name: str) -> float:
        for skill in profile.skills:
            if skill.name == skill_name:
                return skill.score
        return 0.0

    @staticmethod
    def _next_level_hint(profile: GameMasterProfile, score: float) -> str:
        if score < 0.60:
            return "repeat_current_level"
        index = LEVELS.index(profile.level)
        if score >= 0.82 and index < len(LEVELS) - 1:
            return LEVELS[index + 1]
        return profile.level


def default_gamemaster_academy() -> GameMasterAcademy:
    return GameMasterAcademy()


__all__ = [
    "AcademyEvaluation",
    "EvaluationRubric",
    "GameMasterAcademy",
    "GameMasterProfile",
    "SkillScore",
    "TrainingQuest",
    "default_gamemaster_academy",
]
