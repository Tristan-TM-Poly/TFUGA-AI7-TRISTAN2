"""Deterministic agent harness for plan → act → verify loops."""

from __future__ import annotations

from dataclasses import replace

from .bayes_tristan import BayesTristanEngine
from .ip_classifier import IPClassifier
from .models import AgentStep, TheoryCard
from .oak_eval import OAKEvaluator
from .revenue_mapper import RevenueMapper
from .theory_to_prototype import TheoryPrototypeFactory


class AgentHarness:
    """Minimal OAK-safe orchestration harness.

    The harness does not pretend to autonomously execute external actions. It
    produces explicit steps, checks, and reports that can be connected to tools
    later with human/OAK approval gates where needed.
    """

    def __init__(self) -> None:
        self.factory = TheoryPrototypeFactory()
        self.oak = OAKEvaluator()
        self.bayes = BayesTristanEngine()
        self.ip = IPClassifier()
        self.revenue = RevenueMapper()

    def plan(self, idea: str) -> list[AgentStep]:
        """Create the canonical Ω-AI-Tristan action sequence."""

        return [
            AgentStep(
                name="formalize",
                action="Convert rough idea into TheoryCard.",
                expected_output="TheoryCard with purpose, inputs, outputs, tests, risks, next action.",
                oak_check="Card must include tests and risks.",
            ),
            AgentStep(
                name="oak_evaluate",
                action="Run OAK evaluator on the card.",
                expected_output="OAKReport with score, gaps, negative memory, next action.",
                oak_check="No OAK_PASS unless tests and evidence exist.",
            ),
            AgentStep(
                name="bayes_score",
                action="Compute Bayes-Tristan multi-axis score.",
                expected_output="truth/utility/fertility/testability/safety/novelty/revenue/compressibility scores.",
                oak_check="Safety and testability must stay separated from novelty and revenue.",
            ),
            AgentStep(
                name="ip_gate",
                action="Classify public/private/IP risk.",
                expected_output="IP classification with blocked and safe actions.",
                oak_check="IP_LOCK blocks public enabling disclosure.",
            ),
            AgentStep(
                name="revenue_map",
                action="Generate revenue hypotheses with validation tests.",
                expected_output="List of revenue paths with customers, tests, risks, and confidence.",
                oak_check="No guaranteed revenue claims.",
            ),
        ]

    def run(self, idea: str) -> dict[str, object]:
        """Run the local deterministic pipeline and return a report dictionary."""

        steps = self.plan(idea)
        completed_steps = [replace(step, done=True) for step in steps]
        card = self.factory.from_idea(idea)
        oak_report = self.oak.evaluate_theory(card)
        bayes_score = self.bayes.score_theory(card)
        ip_classification = self.ip.classify(card)
        revenue_paths = self.revenue.map_paths(card)

        return {
            "idea": idea,
            "steps": completed_steps,
            "theory_card": card,
            "oak_report": oak_report,
            "bayes_score": bayes_score,
            "bayes_decision": self.bayes.decision_label(bayes_score),
            "ip_classification": ip_classification,
            "revenue_paths": revenue_paths,
        }

    def run_card(self, card: TheoryCard) -> dict[str, object]:
        """Evaluate an already-structured theory card."""

        oak_report = self.oak.evaluate_theory(card)
        bayes_score = self.bayes.score_theory(card)
        return {
            "theory_card": card,
            "oak_report": oak_report,
            "bayes_score": bayes_score,
            "bayes_decision": self.bayes.decision_label(bayes_score),
            "ip_classification": self.ip.classify(card),
            "revenue_paths": self.revenue.map_paths(card),
        }
