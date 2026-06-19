"""Ω-ST v2 executable extensions.

This module turns the plus-ultra Sciences de Tristan design into a small,
auditable Python layer: claim transmutation, memory-negative rules, promotion
checks, canon scoring, OAKCourt review, residues and dashboard reporting.

It intentionally uses only the standard library and stays heuristic: it is a
scientific hygiene layer, not a proof engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from .science_card import OAKStatus, ScienceCard


class OAKDecision(str, Enum):
    PROMOTE = "promote"
    HOLD = "hold"
    SPLIT = "split"
    TRANSMUTE = "transmute"
    REJECT = "reject"


@dataclass(frozen=True)
class CanonScore:
    evidence: float = 0.0
    reproducibility: float = 0.0
    validated_prototype: float = 0.0
    truth: float = 0.5
    known_limits: float = 0.0
    stability: float = 0.5

    def value(self) -> float:
        parts = {
            "evidence": self.evidence,
            "reproducibility": self.reproducibility,
            "validated_prototype": self.validated_prototype,
            "truth": self.truth,
            "known_limits": self.known_limits,
            "stability": self.stability,
        }
        for name, value in parts.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1], got {value!r}")
        return (
            0.25 * self.evidence
            + 0.20 * self.reproducibility
            + 0.20 * self.validated_prototype
            + 0.15 * self.truth
            + 0.10 * self.known_limits
            + 0.10 * self.stability
        )

    @classmethod
    def from_card(cls, card: ScienceCard) -> "CanonScore":
        # Conservative defaults: a card with tests and limits is still not canon
        # until evidence and reproducibility are explicitly recorded.
        evidence = min(len(card.positive_memory), 3) / 3
        known_limits = 1.0 if card.negative_memory or card.residues else 0.25
        validated_prototype = 0.40 if card.tests else 0.0
        return cls(
            evidence=evidence,
            reproducibility=0.0,
            validated_prototype=validated_prototype,
            truth=card.bayes_tristan.true,
            known_limits=known_limits,
            stability=card.bayes_tristan.safe,
        )


@dataclass
class PromotionGateResult:
    source: str
    target: str
    passed: bool
    missing: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "passed": self.passed,
            "missing": list(self.missing),
            "blockers": list(self.blockers),
        }


class PromotionGates:
    """Minimal OAK promotion gate checker."""

    REQUIREMENTS: dict[tuple[str, str], list[str]] = {
        ("Omega_0", "Omega_1"): ["name", "branch", "statement"],
        ("Omega_1", "Omega_2"): ["assumptions", "predictions", "falsifiers_or_tests"],
        ("Omega_2", "Omega_3"): ["prototype_plan", "baseline", "metric"],
        ("Omega_3", "Omega_4"): ["executed_test", "benchmark_result", "recorded_residue"],
        ("Omega_4", "Omega_5"): ["repeated_runs", "ablation", "robustness_check"],
        ("Omega_5", "Omega_6"): ["proof_or_strong_validation", "limitations", "external_comparison"],
        ("Omega_6", "Omega_7"): ["usable_tool", "documentation", "reproducible_example"],
        ("Omega_7", "Omega_8"): ["stable_integration", "canonical_documentation", "long_term_maintenance"],
    }

    def check(self, card: ScienceCard, target: OAKStatus) -> PromotionGateResult:
        source = card.status_oak.value
        requirements = self.REQUIREMENTS.get((source, target.value), [])
        missing = [req for req in requirements if not self._has_requirement(card, req)]
        blockers = []
        if target.rank < card.status_oak.rank:
            blockers.append("target status is lower than current status")
        if target.rank - card.status_oak.rank > 1:
            blockers.append("promotion must move one OAK gate at a time")
        return PromotionGateResult(
            source=source,
            target=target.value,
            passed=not missing and not blockers,
            missing=missing,
            blockers=blockers,
        )

    def _has_requirement(self, card: ScienceCard, requirement: str) -> bool:
        if requirement in {"name", "branch", "statement"}:
            return bool(getattr(card, requirement))
        if requirement == "assumptions":
            return bool(card.assumptions)
        if requirement == "predictions":
            return bool(card.predictions)
        if requirement == "falsifiers_or_tests":
            return bool(card.tests)
        if requirement == "prototype_plan":
            return any("prototype" in action.lower() or "build" in action.lower() for action in card.next_actions)
        if requirement == "baseline":
            return bool(card.baselines)
        if requirement == "metric":
            return any(test.get("metric") for test in card.tests)
        if requirement == "recorded_residue":
            return bool(card.residues)
        if requirement == "limitations":
            return bool(card.negative_memory or card.residues)
        # Later gates require artifacts not represented in the v1 card yet.
        return False


@dataclass
class ClaimTransmutation:
    raw_claim: str
    safe_claim: str
    testable_claim: str
    falsifiers: list[str]
    promotion_path: dict[str, str]
    triggered_rules: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw_claim": self.raw_claim,
            "safe_claim": self.safe_claim,
            "testable_claim": self.testable_claim,
            "falsifiers": list(self.falsifiers),
            "promotion_path": dict(self.promotion_path),
            "triggered_rules": list(self.triggered_rules),
        }


class ClaimTransmuter:
    """Convert over-strong claims into safe, testable claims."""

    HYPE_REPLACEMENTS = {
        "proves": "provides a candidate pathway to test",
        "prove": "provide a candidate pathway to test",
        "solves": "proposes a framework for",
        "guaranteed": "hypothesized under conditions",
        "infinite": "unbounded in the model, subject to physical limits",
        "universal": "broadly applicable candidate",
        "revolutionary": "potentially useful if validated",
    }

    def transmute(self, claim: str, branch: str | None = None) -> ClaimTransmutation:
        lowered = claim.lower()
        triggered: list[str] = []
        safe = claim.strip()
        for raw, replacement in self.HYPE_REPLACEMENTS.items():
            if raw in lowered:
                triggered.append(f"anti_hype:{raw}")
                safe = safe.replace(raw, replacement)
                safe = safe.replace(raw.capitalize(), replacement.capitalize())

        if self._is_material_overclaim(lowered, branch):
            triggered.append("M_MINUS_PHYS_001:no_material_claim_without_measurement")
            safe = (
                "Les géométries conductrices fractales peuvent être explorées comme candidates "
                "pour produire des modes résonants, localisés ou topologiques dans des réseaux simulés. "
                "Une revendication de supraconductivité exige des critères physiques supplémentaires : "
                "résistance nulle, effet Meissner, gap, cohérence de phase et reproductibilité expérimentale."
            )
            testable = (
                "Un réseau LC/RLC fractal conducteur devrait produire une signature spectrale multi-échelle "
                "distinguable de réseaux réguliers ou aléatoires."
            )
        else:
            if not safe.lower().startswith(("candidate", "hypothesis", "hypothèse", "candidate / exploratory")):
                safe = "Candidate / exploratory: " + safe
            testable = "Define a measurable prediction, baseline, metric and falsifier for this claim."

        return ClaimTransmutation(
            raw_claim=claim,
            safe_claim=safe,
            testable_claim=testable,
            falsifiers=[
                "no robust difference versus baselines",
                "effect disappears under ablation or perturbation",
                "signal is explained by numerical or dataset artifact",
                "no measurable prediction can be formulated",
            ],
            promotion_path={
                "Omega_1": "define the object and safe claim",
                "Omega_2": "add assumptions, predictions and falsifiers",
                "Omega_3": "build minimal prototype or simulation",
                "Omega_4": "compare against baselines and record residues",
                "Omega_5": "repeat, ablate and test robustness",
                "Omega_6": "provide proof or strong empirical validation",
            },
            triggered_rules=triggered,
        )

    def _is_material_overclaim(self, lowered: str, branch: str | None) -> bool:
        material_terms = ["superconduct", "supraconduct", "zero resistance", "meissner", "topological phase"]
        return (branch in {"physics", "materials"} or "fractal" in lowered) and any(term in lowered for term in material_terms)


@dataclass(frozen=True)
class MemoryMinusRule:
    id: str
    name: str
    branches: tuple[str, ...]
    keywords: tuple[str, ...]
    required_checks: tuple[str, ...]
    actions: tuple[str, ...]


class MemoryMinusEngine:
    """Detect triggered anti-rules from a ScienceCard."""

    RULES = (
        MemoryMinusRule(
            id="M_MINUS_PHYS_001",
            name="no_material_claim_without_measurement",
            branches=("physics", "materials"),
            keywords=("superconduct", "supraconduct", "zero resistance", "topological phase", "infinite"),
            required_checks=("units", "dimensional_analysis", "physical_mechanism", "measurable_prediction", "baseline", "falsifier", "experimental_criterion"),
            actions=("transmute_claim", "lower_oak_status", "require_test"),
        ),
        MemoryMinusRule(
            id="M_MINUS_MATH_001",
            name="no_theorem_without_definitions",
            branches=("mathematics",),
            keywords=("theorem", "proof", "solves", "demonstrates"),
            required_checks=("definitions", "assumptions", "domain", "proof_steps", "counterexample_search"),
            actions=("block_promotion_to_Omega_6",),
        ),
        MemoryMinusRule(
            id="M_MINUS_ALG_001",
            name="no_exotic_algebra_without_invariant",
            branches=("mathematics", "signals", "ffwt_hac_cvcd"),
            keywords=("quaternion", "octonion", "sedenion", "hypernumber"),
            required_checks=("real_projection", "invariant_measured", "baseline_comparison", "numerical_stability", "interpretability"),
            actions=("require_ablation",),
        ),
        MemoryMinusRule(
            id="M_MINUS_AI_001",
            name="no_agent_without_benchmark",
            branches=("ait_sage",),
            keywords=("ait", "agent", "autonomous", "improves"),
            required_checks=("task", "metric", "baseline", "failure_modes", "evaluation_set"),
            actions=("require_benchmark",),
        ),
    )

    def detect(self, card: ScienceCard) -> list[dict[str, Any]]:
        text = f"{card.name} {card.statement}".lower()
        matches: list[dict[str, Any]] = []
        for rule in self.RULES:
            branch_match = card.branch in rule.branches or not rule.branches
            keyword_match = any(keyword in text for keyword in rule.keywords)
            if branch_match and keyword_match:
                matches.append(
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "required_checks": list(rule.required_checks),
                        "actions": list(rule.actions),
                    }
                )
        return matches


@dataclass
class Residue:
    source: str
    gap: str
    possible_causes: list[str] = field(default_factory=list)
    fertility_score: float = 0.5


class ResidueMiner:
    """Transform structured residues into child hypothesis seeds."""

    def mine(self, residue: Residue) -> list[dict[str, Any]]:
        causes = residue.possible_causes or ["unknown mechanism", "missing feature", "bad baseline"]
        children = []
        for index, cause in enumerate(causes, start=1):
            children.append(
                {
                    "id": f"CHILD-{index}",
                    "claim": f"Investigate whether {cause} explains residue: {residue.gap}",
                    "source": residue.source,
                    "fertility_score": residue.fertility_score,
                    "next_test": f"Design a controlled test for cause: {cause}",
                }
            )
        return children


@dataclass
class ScienceOrganism:
    card: ScienceCard
    genome: dict[str, Any] = field(default_factory=dict)
    phenotype: dict[str, Any] = field(default_factory=dict)
    metabolism: dict[str, Any] = field(default_factory=dict)
    immune_system: dict[str, Any] = field(default_factory=dict)
    embodiment: dict[str, Any] = field(default_factory=dict)
    reproduction: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "card": self.card.as_dict(),
            "genome": self.genome,
            "phenotype": self.phenotype,
            "metabolism": self.metabolism,
            "immune_system": self.immune_system,
            "embodiment": self.embodiment,
            "reproduction": self.reproduction,
        }

    @classmethod
    def from_card(cls, card: ScienceCard) -> "ScienceOrganism":
        transmutation = ClaimTransmuter().transmute(card.statement, branch=card.branch)
        memory_triggers = MemoryMinusEngine().detect(card)
        return cls(
            card=card,
            genome={
                "statement": card.statement,
                "assumptions": card.assumptions,
                "predictions": card.predictions,
                "falsifiers": [test.get("falsifier") for test in card.tests if test.get("falsifier")],
            },
            phenotype={
                "branch": card.branch,
                "visible_claim": card.statement,
                "safe_claim": transmutation.safe_claim,
            },
            metabolism={
                "inputs": ["data", "corpus", "equations", "signals"],
                "transformations": ["HGFM", "LOG", "CVCD", "EXP", "BayesT", "OAK"],
                "outputs": ["tests", "prototypes", "reports", "residues", "papers"],
            },
            immune_system={
                "memory_negative": memory_triggers,
                "claim_transmutation": transmutation.as_dict(),
            },
            embodiment={
                "baselines": card.baselines,
                "tests": card.tests,
                "metrics": [test.get("metric") for test in card.tests if test.get("metric")],
            },
            reproduction={
                "child_hypotheses": [],
                "next_actions": card.next_actions,
            },
        )


@dataclass
class OAKCourtReview:
    claim_id: str
    claim: str
    strongest_version: str
    safe_version: str
    prosecutor: dict[str, Any]
    defender: dict[str, Any]
    experimentalist: dict[str, Any]
    engineer: dict[str, Any]
    memory_minus: dict[str, Any]
    verdict: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim": self.claim,
            "strongest_version": self.strongest_version,
            "safe_version": self.safe_version,
            "prosecutor": self.prosecutor,
            "defender": self.defender,
            "experimentalist": self.experimentalist,
            "engineer": self.engineer,
            "memory_minus": self.memory_minus,
            "verdict": self.verdict,
        }


class OAKCourt:
    """Multi-role OAK review scaffold."""

    def review(self, card: ScienceCard) -> OAKCourtReview:
        transmutation = ClaimTransmuter().transmute(card.statement, branch=card.branch)
        memory_rules = MemoryMinusEngine().detect(card)
        canon = CanonScore.from_card(card).value()
        decision = self._decision(card, memory_rules, canon)
        blockers = []
        if memory_rules:
            blockers.append("memory-minus rules triggered")
        if card.needs_oak_review():
            blockers.append("Omega_2+ card lacks explicit tests")
        if canon < 0.5:
            blockers.append("canon score below promotion threshold")

        return OAKCourtReview(
            claim_id=card.id,
            claim=card.statement,
            strongest_version=card.statement,
            safe_version=transmutation.safe_claim,
            prosecutor={
                "objections": blockers or ["no fatal objection recorded yet"],
                "possible_failure_modes": [
                    "undefined terms",
                    "bad baseline",
                    "data or simulation artifact",
                    "fertility confused with truth",
                ],
            },
            defender={
                "strongest_arguments": [
                    "fertile if it generates tests and prototypes",
                    "safe if kept at current OAK status until evidence improves",
                ],
                "protected_core": transmutation.testable_claim,
            },
            experimentalist={
                "minimal_test": card.tests[0] if card.tests else {"name": "define_minimal_test", "metric": "missing"},
                "baselines": card.baselines,
                "falsifiers": transmutation.falsifiers,
            },
            engineer={
                "minimal_prototype": card.next_actions[0] if card.next_actions else "write a prototype plan",
                "expected_runtime": "unknown",
                "dependencies": [],
            },
            memory_minus={
                "triggered_anti_rules": memory_rules,
                "forbidden_promotions": ["do not promote high fertility as proof"],
            },
            verdict={
                "current_status": card.status_oak.value,
                "recommended_status": card.status_oak.value if decision != OAKDecision.TRANSMUTE else "Omega_1",
                "decision": decision.value,
                "canon_score": round(canon, 4),
                "promotion_blockers": blockers,
                "next_action": card.next_actions[0] if card.next_actions else "add tests, baselines, falsifiers and prototype plan",
            },
        )

    def _decision(self, card: ScienceCard, memory_rules: list[dict[str, Any]], canon_score: float) -> OAKDecision:
        if memory_rules:
            return OAKDecision.TRANSMUTE
        if card.needs_oak_review():
            return OAKDecision.HOLD
        if canon_score >= 0.75 and card.status_oak.rank >= 4:
            return OAKDecision.PROMOTE
        return OAKDecision.HOLD


def portfolio_dashboard(cards: Iterable[ScienceCard]) -> dict[str, Any]:
    cards = list(cards)
    by_branch: dict[str, int] = {}
    by_status: dict[str, int] = {}
    high_risk = []
    top_priority = []
    top_canon = []
    memory_engine = MemoryMinusEngine()
    for card in cards:
        by_branch[card.branch] = by_branch.get(card.branch, 0) + 1
        by_status[card.status_oak.value] = by_status.get(card.status_oak.value, 0) + 1
        priority = card.priority()
        canon = CanonScore.from_card(card).value()
        item = {"id": card.id, "name": card.name, "priority": round(priority, 4), "canon_score": round(canon, 4)}
        top_priority.append(item)
        top_canon.append(item)
        triggers = memory_engine.detect(card)
        if triggers:
            high_risk.append({"id": card.id, "name": card.name, "triggers": triggers})
    return {
        "total_cards": len(cards),
        "by_branch": by_branch,
        "by_oak_status": by_status,
        "top_priority": sorted(top_priority, key=lambda x: x["priority"], reverse=True)[:10],
        "top_canon_candidates": sorted(top_canon, key=lambda x: x["canon_score"], reverse=True)[:10],
        "high_risk_claims": high_risk,
        "oak_gaps": [{"id": card.id, "name": card.name} for card in cards if card.needs_oak_review()],
    }
