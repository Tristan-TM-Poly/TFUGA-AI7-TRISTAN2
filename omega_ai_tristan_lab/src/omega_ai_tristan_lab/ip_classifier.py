"""Preliminary IP classifier for Ω-AI-TRISTAN-LAB.

This module is not legal advice. It exists to prevent accidental disclosure and
force an explicit OAK/IP gate before publishing inventions.
"""

from __future__ import annotations

from .models import IPClassification, TheoryCard


class IPClassifier:
    """Classify a theory/prototype into a conservative IP bucket."""

    PUBLIC_KEYWORDS = {"tutorial", "course", "template", "readme", "example"}
    PATENT_KEYWORDS = {"patent", "brevet", "invention", "novel device", "apparatus", "method"}
    SECRET_KEYWORDS = {"secret", "private", "proprietary", "confidential", "trade secret"}
    OPEN_SOURCE_KEYWORDS = {"open-source", "github", "oss", "license", "contribution"}

    def classify(self, card: TheoryCard) -> IPClassification:
        text = " ".join([
            card.name,
            card.purpose,
            " ".join(card.inputs),
            " ".join(card.outputs),
            " ".join(card.risks),
            " ".join(card.revenue_hypotheses),
        ]).lower()

        if self._contains(text, self.PATENT_KEYWORDS):
            return IPClassification(
                label="IP_LOCK_PATENT_REVIEW",
                confidence=0.78,
                rationale=[
                    "Potential patent/invention language detected.",
                    "Public disclosure could reduce future IP options.",
                ],
                safe_public_actions=[
                    "Publish only high-level non-enabling summaries.",
                    "Keep implementation details private until prior-art review.",
                ],
                blocked_actions=[
                    "Do not publish claims, diagrams, code, or full enabling details yet.",
                    "Do not send commercial blasts before IP/legal review.",
                ],
                next_action="Prepare a private invention disclosure memo and prior-art search.",
            )

        if self._contains(text, self.SECRET_KEYWORDS):
            return IPClassification(
                label="TRADE_SECRET_CANDIDATE",
                confidence=0.72,
                rationale=["Confidential/proprietary language detected."],
                safe_public_actions=["Publish only sanitized capability statements."],
                blocked_actions=["Do not expose algorithms, datasets, keys, or workflows."],
                next_action="Create access-control, provenance, and disclosure logs.",
            )

        if self._contains(text, self.OPEN_SOURCE_KEYWORDS):
            return IPClassification(
                label="OPEN_SOURCE_REVIEW",
                confidence=0.68,
                rationale=["Open-source/GitHub pathway detected."],
                safe_public_actions=[
                    "Choose a license deliberately.",
                    "Add provenance and attribution if external code influenced the work.",
                ],
                blocked_actions=["Do not mix incompatible licensed code."],
                next_action="Run license/provenance check before release.",
            )

        if self._contains(text, self.PUBLIC_KEYWORDS):
            return IPClassification(
                label="PUBLIC_EDUCATIONAL_ASSET",
                confidence=0.64,
                rationale=["Educational/template orientation detected."],
                safe_public_actions=["Publish as docs, course notes, or examples after review."],
                blocked_actions=["Avoid implying certification, guaranteed results, or legal advice."],
                next_action="Add disclaimers, tests, and public README.",
            )

        return IPClassification(
            label="UNCLASSIFIED_NEEDS_REVIEW",
            confidence=0.50,
            rationale=["No strong IP bucket detected."],
            safe_public_actions=["Share only non-sensitive summaries."],
            blocked_actions=["Avoid public release until OAK/IP classification is explicit."],
            next_action="Decide whether this is open/public, paper, patent, trade secret, or service.",
        )

    @staticmethod
    def _contains(text: str, keywords: set[str]) -> bool:
        return any(keyword in text for keyword in keywords)
