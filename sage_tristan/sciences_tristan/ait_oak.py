"""AIT-OAK: heuristic falsification and promotion assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .science_card import OAKStatus, ScienceCard


@dataclass
class OAKReview:
    card_id: str
    card_name: str
    safe_claim: str
    status_oak: str
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    suggested_baselines: list[str] = field(default_factory=list)
    suggested_tests: list[dict[str, str]] = field(default_factory=list)
    falsifiers: list[str] = field(default_factory=list)
    next_action: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "card_name": self.card_name,
            "safe_claim": self.safe_claim,
            "status_oak": self.status_oak,
            "strengths": list(self.strengths),
            "risks": list(self.risks),
            "suggested_baselines": list(self.suggested_baselines),
            "suggested_tests": list(self.suggested_tests),
            "falsifiers": list(self.falsifiers),
            "next_action": self.next_action,
        }


class AITOAK:
    """Generate a first-pass OAK review from a ScienceCard.

    This is not a proof engine. It is a hygiene engine that forces each card
    to expose baselines, tests, falsifiers and safe wording.
    """

    DEFAULT_BASELINES = {
        "ffwt_hac_cvcd": ["FFT", "classical wavelets", "STFT", "PCA/SVD", "statistical features"],
        "signals": ["FFT", "classical wavelets", "STFT", "PCA/SVD", "statistical features"],
        "physics": ["regular lattice", "random graph", "analytic limiting case", "dimensional analysis"],
        "materials": ["known reference material", "published spectrum", "randomized spectrum", "classical peak fitting"],
        "bayes_tristan": ["manual ranking", "truth-only ranking", "fertility-only ranking", "random ranking"],
        "hgfm": ["flat tag list", "ordinary graph", "manual map"],
        "negative_memory": ["unfiltered generation", "manual review only"],
    }

    def review(self, card: ScienceCard) -> OAKReview:
        baselines = list(card.baselines) or self.DEFAULT_BASELINES.get(card.branch, ["manual baseline"])
        tests = list(card.tests) or [self._default_test(card)]
        risks = self._risks(card)
        falsifiers = self._falsifiers(card, tests)
        next_action = card.next_actions[0] if card.next_actions else self._default_next_action(card)

        return OAKReview(
            card_id=card.id,
            card_name=card.name,
            safe_claim=card.safe_statement(),
            status_oak=self._recommended_status(card).value,
            strengths=self._strengths(card),
            risks=risks,
            suggested_baselines=baselines,
            suggested_tests=[self._normalize_test(test) for test in tests],
            falsifiers=falsifiers,
            next_action=next_action,
        )

    def _recommended_status(self, card: ScienceCard) -> OAKStatus:
        if card.tests and card.status_oak.rank < 3:
            return OAKStatus.OMEGA_3
        if not card.tests and card.status_oak.rank > 2:
            return OAKStatus.OMEGA_2
        return card.status_oak

    def _strengths(self, card: ScienceCard) -> list[str]:
        strengths: list[str] = []
        vector = card.bayes_tristan
        if vector.testable >= 0.75:
            strengths.append("high testability")
        if vector.fertile >= 0.75:
            strengths.append("high fertility")
        if vector.safe >= 0.80:
            strengths.append("safe to explore with explicit limits")
        if card.next_actions:
            strengths.append("has at least one concrete next action")
        return strengths or ["needs clearer strengths"]

    def _risks(self, card: ScienceCard) -> list[str]:
        risks = list(card.negative_memory)
        if card.bayes_tristan.true < 0.50 and card.bayes_tristan.fertile > 0.75:
            risks.append("high fertility but low truth-score: keep as candidate, not canon")
        if card.status_oak.rank >= 2 and not card.tests:
            risks.append("Omega_2+ card lacks explicit tests")
        if card.branch in {"physics", "materials"}:
            risks.append("avoid promoting mechanism or geometry into empirical property without measurement")
        return risks or ["no major risk recorded yet"]

    def _default_test(self, card: ScienceCard) -> dict[str, str]:
        return {
            "name": f"oak_minimal_test_{card.id.lower()}",
            "metric": "explicit measurable metric required",
            "success_condition": "beats or clarifies a relevant baseline",
            "falsifier": "no measurable improvement or no interpretable invariant after controlled comparison",
            "cost": "unknown",
        }

    def _normalize_test(self, test: dict[str, Any]) -> dict[str, str]:
        return {
            "name": str(test.get("name", "unnamed_test")),
            "metric": str(test.get("metric", "missing metric")),
            "success_condition": str(test.get("success_condition", "missing success condition")),
            "falsifier": str(test.get("falsifier", "missing falsifier")),
            "cost": str(test.get("cost", "unknown")),
        }

    def _falsifiers(self, card: ScienceCard, tests: list[dict[str, Any]]) -> list[str]:
        falsifiers = [str(test.get("falsifier")) for test in tests if test.get("falsifier")]
        if not falsifiers:
            falsifiers.append("No falsifier specified; card cannot promote beyond Omega_2.")
        return falsifiers

    def _default_next_action(self, card: ScienceCard) -> str:
        if card.status_oak.rank <= 1:
            return "Write a precise statement, assumptions, predictions, baseline and minimal OAK test."
        if card.status_oak.rank == 2:
            return "Build the smallest prototype or simulation that can falsify the claim."
        if card.status_oak.rank == 3:
            return "Run the prototype against a baseline and record residues."
        return "Audit reproducibility, limits and promotion criteria."
