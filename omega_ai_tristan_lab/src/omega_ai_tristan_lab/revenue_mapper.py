"""Revenue mapping for Ω-AI-TRISTAN-LAB.

The mapper generates hypotheses, not promises. Every path includes a validation
test and risks so revenue thinking stays OAK-safe.
"""

from __future__ import annotations

from .models import RevenuePath, TheoryCard


class RevenueMapper:
    """Map a theory card to plausible revenue paths."""

    def map_paths(self, card: TheoryCard) -> list[RevenuePath]:
        text = " ".join([
            card.name,
            card.purpose,
            " ".join(card.outputs),
            " ".join(card.revenue_hypotheses),
        ]).lower()
        paths: list[RevenuePath] = []

        paths.append(
            RevenuePath(
                name="Expert audit / consulting sprint",
                customer="SME, startup, research lab, or professor with a concrete AI workflow",
                value_proposition="Turn a vague AI idea into a tested prototype plan with OAK risks and next actions.",
                validation_test="Offer one 60-90 minute paid diagnostic or free pilot with clear before/after artifact.",
                risks=["Scope creep", "overpromising", "unclear buyer pain"],
                effort="low-to-medium",
                confidence=0.62,
            )
        )

        if any(term in text for term in ["rag", "pdf", "paper", "document", "latex"]):
            paths.append(
                RevenuePath(
                    name="Document-to-prototype agent",
                    customer="Students, professors, R&D teams, technical founders",
                    value_proposition="Convert papers/PDFs into summaries, LaTeX notes, code skeletons, tests, and OAK reports.",
                    validation_test="Process 5 documents for one real user and measure time saved + correction rate.",
                    risks=["Copyright limits", "citation accuracy", "hallucinated claims"],
                    effort="medium",
                    confidence=0.68,
                )
            )

        if any(term in text for term in ["github", "open-source", "repo", "stackoverflow"]):
            paths.append(
                RevenuePath(
                    name="OSS digestion and adaptation service",
                    customer="Developers and small teams integrating open-source tools",
                    value_proposition="Score repos, extract patterns, check licenses, and produce safe adaptation plans.",
                    validation_test="Run on 3 candidate repos and compare saved integration time vs manual review.",
                    risks=["License incompatibility", "supply-chain risk", "stale dependencies"],
                    effort="medium",
                    confidence=0.64,
                )
            )

        if any(term in text for term in ["course", "template", "curriculum", "education"]):
            paths.append(
                RevenuePath(
                    name="AI systems course / template pack",
                    customer="Self-learners, engineering students, technical operators",
                    value_proposition="A practical course where every lesson creates a reusable artifact.",
                    validation_test="Publish a small free module and measure signups, completion, and feedback.",
                    risks=["Crowded market", "low willingness to pay", "maintenance load"],
                    effort="medium-to-high",
                    confidence=0.55,
                )
            )

        paths.append(
            RevenuePath(
                name="Private prototype licensing",
                customer="Organizations needing a specialized OAK-safe agent workflow",
                value_proposition="License a verified workflow component instead of a generic AI demo.",
                validation_test="Get one letter of intent or paid customization request before productizing.",
                risks=["IP ambiguity", "support burden", "enterprise sales cycle"],
                effort="high",
                confidence=0.42,
            )
        )
        return paths
