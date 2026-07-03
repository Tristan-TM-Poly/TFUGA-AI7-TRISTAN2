"""OAK evaluator: Operational Anti-hallucination Kernel.

The evaluator is intentionally conservative. It rewards testability, explicit
limits, reproducibility, and safe next actions. It penalizes hype, missing
baselines, unsupported claims, and IP/security risks.
"""

from __future__ import annotations

from .models import OAKReport, OAKStatus, TheoryCard


class OAKEvaluator:
    """Rule-based OAK scoring for early-stage ideas and prototypes."""

    def evaluate_theory(self, card: TheoryCard) -> OAKReport:
        strengths: list[str] = []
        weaknesses: list[str] = []
        missing_evidence: list[str] = []
        negative_memory: list[str] = []

        score = 0.0
        score += self._score_presence(card.purpose, 0.12, "purpose", strengths, weaknesses)
        score += self._score_list(card.inputs, 0.08, "inputs", strengths, missing_evidence)
        score += self._score_list(card.outputs, 0.08, "outputs", strengths, missing_evidence)
        score += self._score_list(card.assumptions, 0.10, "assumptions", strengths, missing_evidence)
        score += self._score_list(card.algorithm, 0.14, "algorithm", strengths, missing_evidence)
        score += self._score_list(card.tests, 0.18, "tests", strengths, missing_evidence)
        score += self._score_list(card.risks, 0.12, "risks", strengths, missing_evidence)
        score += self._score_list(card.revenue_hypotheses, 0.08, "revenue hypotheses", strengths, missing_evidence)
        score += self._score_presence(card.next_action, 0.10, "next action", strengths, weaknesses)

        hype_terms = ["guaranteed", "infinite", "perfect", "100%", "revolutionary proof"]
        haystack = " ".join([
            card.name,
            card.purpose,
            " ".join(card.assumptions),
            " ".join(card.revenue_hypotheses),
        ]).lower()
        found_hype = [term for term in hype_terms if term in haystack]
        if found_hype:
            penalty = min(0.20, 0.05 * len(found_hype))
            score -= penalty
            negative_memory.append(f"Hype penalty: unsupported terms {found_hype}")

        if not card.tests:
            negative_memory.append("No tests: keep status at IDEA/MODEL, not proof.")
        if not card.risks:
            negative_memory.append("No explicit risks: add failure modes before public claims.")

        score = max(0.0, min(1.0, score))
        status = self._infer_status(score, card)
        next_action = self._next_action(status, card)

        return OAKReport(
            status=status,
            score=round(score, 3),
            strengths=strengths,
            weaknesses=weaknesses,
            missing_evidence=missing_evidence,
            negative_memory=negative_memory,
            next_action=next_action,
        )

    @staticmethod
    def _score_presence(
        value: str,
        weight: float,
        label: str,
        strengths: list[str],
        gaps: list[str],
    ) -> float:
        if value and value.strip():
            strengths.append(f"Defined {label}.")
            return weight
        gaps.append(f"Missing {label}.")
        return 0.0

    @staticmethod
    def _score_list(
        values: list[str],
        weight: float,
        label: str,
        strengths: list[str],
        gaps: list[str],
    ) -> float:
        if values:
            strengths.append(f"Defined {label}: {len(values)} item(s).")
            return weight
        gaps.append(f"Missing {label}.")
        return 0.0

    @staticmethod
    def _infer_status(score: float, card: TheoryCard) -> OAKStatus:
        if "patent" in " ".join(card.risks + card.revenue_hypotheses).lower():
            return OAKStatus.IP_LOCK
        if score >= 0.86 and card.tests:
            return OAKStatus.OAK_PASS
        if score >= 0.72 and card.tests:
            return OAKStatus.TESTED
        if score >= 0.50 and card.algorithm:
            return OAKStatus.MODEL
        return OAKStatus.IDEA

    @staticmethod
    def _next_action(status: OAKStatus, card: TheoryCard) -> str:
        if status == OAKStatus.IP_LOCK:
            return "Freeze public disclosure; prepare private IP memo and prior-art search."
        if status == OAKStatus.OAK_PASS:
            return "Create benchmark comparison and decide publish/open-source/IP route."
        if status == OAKStatus.TESTED:
            return "Run baseline benchmark and record residuals."
        if status == OAKStatus.MODEL:
            return "Implement the smallest prototype and add one failing test first."
        return card.next_action or "Write a falsifiable theory card."
