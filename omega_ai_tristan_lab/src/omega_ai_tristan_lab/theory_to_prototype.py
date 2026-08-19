"""Convert rough ideas into structured TheoryCard objects."""

from __future__ import annotations

import re

from .models import OAKStatus, TheoryCard


class TheoryPrototypeFactory:
    """Heuristic idea-to-card transformer.

    This is deliberately lightweight and deterministic so it can be tested
    without external LLM dependencies. Future versions can call an LLM behind
    the same interface.
    """

    def from_idea(self, idea: str, name: str | None = None) -> TheoryCard:
        cleaned = " ".join(idea.strip().split())
        title = name or self._make_name(cleaned)
        tokens = set(re.findall(r"[a-zA-ZÀ-ÿ0-9_-]+", cleaned.lower()))

        inputs = ["raw idea text", "constraints", "available evidence"]
        outputs = ["theory card", "prototype plan", "OAK report", "next action"]
        assumptions = [
            "The idea is treated as fertile but unproven until tested.",
            "A minimal prototype is preferred over a large speculative system.",
        ]
        algorithm = [
            "Normalize the idea and extract purpose.",
            "Identify inputs, outputs, assumptions, tests, risks, and revenue hypotheses.",
            "Run OAK evaluation and Bayes-Tristan scoring.",
            "Choose the smallest falsifiable prototype.",
        ]
        tests = [
            "Create one deterministic unit test for the transformation pipeline.",
            "Check that every generated card includes risks and next_action.",
        ]
        risks = [
            "Hallucinated capabilities if claims are not benchmarked.",
            "Original or confidential details should be classified before public release.",
        ]
        revenue = [
            "Consulting/audit if the prototype solves a real workflow.",
            "Template/course/SaaS only after user validation and repeatable demand.",
        ]

        if {"pdf", "latex", "paper", "article"} & tokens:
            inputs.extend(["PDF or paper", "bibliographic metadata"])
            outputs.extend(["LaTeX summary", "code skeleton", "citation ledger"])
            tests.append("Compare extracted claims against source citations.")
            risks.append("Copyright/licensing limits on full-text reproduction.")
        if {"github", "repo", "open-source", "stackoverflow"} & tokens:
            inputs.extend(["repository URL", "license", "issues/PRs"])
            outputs.extend(["license gate", "provenance ledger", "safe adaptation plan"])
            tests.append("Verify license compatibility and attribution requirements.")
            risks.append("Supply-chain, outdated snippet, and license incompatibility risk.")
        if {"agent", "ait", "sage", "workflow"} & tokens:
            inputs.extend(["goal", "tools", "memory", "verification rules"])
            outputs.extend(["agent plan", "action log", "verification log"])
            tests.append("Inject a failing step and verify the harness records the residual.")
        if {"brevet", "patent", "ip", "invention"} & tokens:
            risks.append("Potential patentability: use IP_LOCK until prior-art and counsel review.")
            revenue.append("Potential licensing path after private IP assessment.")
            status = OAKStatus.IP_LOCK
        else:
            status = OAKStatus.MODEL

        return TheoryCard(
            name=title,
            purpose=cleaned or "Transform a raw idea into an OAK-safe prototype path.",
            inputs=sorted(set(inputs)),
            outputs=sorted(set(outputs)),
            assumptions=assumptions,
            algorithm=algorithm,
            tests=tests,
            risks=risks,
            revenue_hypotheses=revenue,
            oak_status=status,
            next_action="Implement the smallest prototype and add tests before public claims.",
        )

    @staticmethod
    def _make_name(idea: str) -> str:
        words = re.findall(r"[A-Za-zÀ-ÿ0-9]+", idea)[:8]
        if not words:
            return "Ω-AI-Tristan Prototype"
        return " ".join(words).strip().title()
