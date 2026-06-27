from __future__ import annotations

import json
from dataclasses import asdict, dataclass


BLOCKED_TERMS = {
    "manipulative_loop",
    "predatory_reward",
    "online_cheat",
    "unsafe_real_world_instruction",
    "addiction_pressure",
    "toxic_content",
}


@dataclass(frozen=True)
class OAKReport:
    accepted: bool
    flags: tuple[str, ...]
    warnings: tuple[str, ...]
    score: float

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"


class OAKGate:
    """Small safety and quality gate for game/simulation events.

    The gate protects agency, fairness, coherence, testability, and safety.
    It prepares review signals only; it does not publish or run external games.
    """

    def __init__(self, blocked_terms: set[str] | None = None) -> None:
        self.blocked_terms = set(blocked_terms or BLOCKED_TERMS)

    def evaluate_text(self, text: str, *, quality_score: float = 1.0) -> OAKReport:
        normalized = text.lower().replace(" ", "_")
        flags = tuple(sorted(term for term in self.blocked_terms if term in normalized))
        warnings: list[str] = []
        if quality_score < 0.65:
            warnings.append("low_game_quality_score")
        if "reward" in normalized and "consent" not in normalized:
            warnings.append("reward_system_needs_consent_review")
        accepted = not flags and quality_score >= 0.5
        score = max(0.0, min(1.0, quality_score - 0.15 * len(flags) - 0.05 * len(warnings)))
        return OAKReport(accepted=accepted, flags=flags, warnings=tuple(warnings), score=round(score, 4))

    def evaluate_payload(self, payload: dict, *, quality_score: float = 1.0) -> OAKReport:
        return self.evaluate_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), quality_score=quality_score)
