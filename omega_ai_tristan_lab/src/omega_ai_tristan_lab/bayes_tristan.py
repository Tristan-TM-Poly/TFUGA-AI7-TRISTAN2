"""Bayes-Tristan multi-axis decision engine.

This is not a replacement for rigorous Bayesian inference. It is a pragmatic
posterior-like scorer that keeps separate axes for truth, utility, fertility,
testability, safety, novelty, revenue, and compressibility.
"""

from __future__ import annotations

from .models import BayesAxisScore, TheoryCard


class BayesTristanEngine:
    """Update multi-axis scores using observed evidence tags."""

    DEFAULT_PRIOR = BayesAxisScore(
        truth=0.45,
        utility=0.50,
        fertility=0.55,
        testability=0.40,
        safety=0.60,
        novelty=0.50,
        revenue=0.35,
        compressibility=0.45,
    )

    EVIDENCE_WEIGHTS: dict[str, BayesAxisScore] = {
        "has_tests": BayesAxisScore(0.10, 0.06, 0.04, 0.20, 0.06, 0.00, 0.03, 0.05),
        "has_benchmark": BayesAxisScore(0.16, 0.08, 0.03, 0.16, 0.05, 0.00, 0.05, 0.06),
        "has_customer_signal": BayesAxisScore(0.02, 0.18, 0.06, 0.04, 0.02, 0.00, 0.20, 0.03),
        "has_prior_art": BayesAxisScore(0.06, 0.03, -0.02, 0.08, 0.10, -0.08, 0.00, 0.03),
        "has_ip_risk": BayesAxisScore(-0.02, -0.02, 0.00, 0.00, -0.16, 0.04, -0.05, 0.00),
        "has_public_claims": BayesAxisScore(-0.04, 0.02, 0.00, 0.00, -0.10, 0.00, 0.02, 0.00),
        "has_clear_invariants": BayesAxisScore(0.12, 0.08, 0.10, 0.10, 0.06, 0.03, 0.02, 0.18),
        "has_negative_memory": BayesAxisScore(0.06, 0.04, 0.06, 0.06, 0.12, 0.00, 0.00, 0.05),
    }

    def score_theory(
        self,
        card: TheoryCard,
        evidence: list[str] | None = None,
        prior: BayesAxisScore | None = None,
    ) -> BayesAxisScore:
        """Return a clamped multi-axis score for a theory card."""

        score = prior or self.DEFAULT_PRIOR
        evidence = list(evidence or [])

        if card.tests:
            evidence.append("has_tests")
        if card.risks:
            evidence.append("has_negative_memory")
        if any("benchmark" in test.lower() for test in card.tests):
            evidence.append("has_benchmark")
        if any("customer" in rev.lower() or "client" in rev.lower() for rev in card.revenue_hypotheses):
            evidence.append("has_customer_signal")
        if any("patent" in item.lower() or "brevet" in item.lower() for item in card.risks + card.revenue_hypotheses):
            evidence.append("has_ip_risk")
        if card.inputs and card.outputs and card.algorithm:
            evidence.append("has_clear_invariants")

        vector = score
        for tag in evidence:
            delta = self.EVIDENCE_WEIGHTS.get(tag)
            if delta is None:
                continue
            vector = BayesAxisScore(
                truth=vector.truth + delta.truth,
                utility=vector.utility + delta.utility,
                fertility=vector.fertility + delta.fertility,
                testability=vector.testability + delta.testability,
                safety=vector.safety + delta.safety,
                novelty=vector.novelty + delta.novelty,
                revenue=vector.revenue + delta.revenue,
                compressibility=vector.compressibility + delta.compressibility,
            ).clamp()
        return vector

    def decision_label(self, score: BayesAxisScore) -> str:
        """Convert weighted total into a conservative action label."""

        total = score.weighted_total()
        if score.safety < 0.42:
            return "OAK-PAUSE: risk or IP/safety uncertainty too high"
        if total >= 0.76:
            return "BUILD: prototype + benchmark"
        if total >= 0.62:
            return "MODEL: formalize + test one core invariant"
        if total >= 0.48:
            return "RESEARCH: collect evidence + counterexamples"
        return "PARK: keep as fertile idea, do not overinvest yet"
