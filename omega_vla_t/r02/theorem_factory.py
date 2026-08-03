"""Deterministic generation of falsifiable Ω-VLA research cells."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .address import FrontierAddress
from .models import EpistemicStatus, ProblemCell, stable_identifier


QUESTION_CONCLUSIONS = {
    "existence": "Establish sufficient conditions for existence of the declared object or solution.",
    "uniqueness": "Determine whether the declared object is unique under the stated hypotheses.",
    "stability": "Bound the response to admissible perturbations and identify instability mechanisms.",
    "convergence": "Prove or falsify convergence under an explicit refinement or iteration regime.",
    "conditioning": "Characterize sensitivity and construct a conditioning certificate.",
    "invariance": "Identify transformations preserving the declared quantities.",
    "compression": "Construct a compressed representation with an explicit residual bound.",
    "identifiability": "Determine which mechanisms are distinguishable from the allowed observations.",
    "controllability": "Characterize reachable states under the declared actuation model.",
    "observability": "Characterize state information recoverable from the declared measurements.",
    "approximation": "Derive an approximation theorem or a falsifying counterexample with error metrics.",
    "counterexample": "Search systematically for the smallest counterexample to the candidate property.",
}


METHOD_REQUIREMENTS = {
    "direct_proof": ("explicit definitions", "complete implication chain"),
    "spectral": ("spectrum or pseudospectrum", "mode sensitivity audit"),
    "variational": ("objective functional", "admissible set", "coercivity or counterexample"),
    "energy_estimate": ("energy functional", "boundary terms", "sign audit"),
    "fixed_point": ("complete metric space", "self-map", "contraction or compactness conditions"),
    "topological": ("chain complex", "boundary consistency", "invariant certificate"),
    "probabilistic": ("probability model", "confidence statement", "calibration audit"),
    "interval_arithmetic": ("bounded domain", "outward rounding", "certificate replay"),
    "formal_assistant": ("formal definitions", "dependency graph", "machine-checkable target"),
    "numerical_falsification": ("finite search domain", "adversarial fixtures", "reproducible seed"),
}


@dataclass(frozen=True)
class TheoremFactory:
    """Compile an address into a research cell without asserting truth."""

    version: str = "R0.2-MAX"

    def generate(self, address: FrontierAddress) -> ProblemCell:
        c = address.as_mapping()
        question = c["question"]
        method = c["method"]
        epistemic = c["epistemic"]

        hypotheses = (
            f"scalar_system={c['scalar']}",
            f"space={c['space']}",
            f"geometry={c['geometry']}",
            f"operator={c['operator']}",
            f"discretization={c['discretization']}",
            f"regime={c['regime']}",
            "all domains, codomains, units and regularity assumptions are explicit",
        )
        invariants = self._invariants(address)
        baselines = self._baselines(address)
        methods = (method, *METHOD_REQUIREMENTS[method])
        falsifiers = self._falsifiers(address)
        expected = self._expected_artifacts(method, question)

        scores = self._scores(address)
        payload = {
            "address": address.canonical(),
            "version": self.version,
        }
        return ProblemCell(
            cell_id=stable_identifier("vla-cell", payload),
            address=address.canonical(),
            object_family=f"{address.layer}/{address.program}",
            hypotheses=hypotheses,
            candidate_conclusion=QUESTION_CONCLUSIONS[question],
            invariants=invariants,
            baselines=baselines,
            methods=methods,
            falsifiers=falsifiers,
            expected_artifacts=expected,
            priority=scores[0],
            novelty_score=scores[1],
            testability_score=scores[2],
            risk_score=scores[3],
            status=self._status(epistemic),
            theorem_claimed=False,
        )

    def generate_many(self, addresses: Iterable[FrontierAddress]) -> list[ProblemCell]:
        return [self.generate(address) for address in addresses]

    @staticmethod
    def _status(value: str) -> EpistemicStatus:
        mapping = {
            "idea": EpistemicStatus.IDEA,
            "defined": EpistemicStatus.DEFINED,
            "numeric_fixture": EpistemicStatus.NUMERICALLY_OBSERVED,
            "proposition": EpistemicStatus.PROPOSITION,
            "counterexample": EpistemicStatus.COUNTEREXAMPLE_FOUND,
            "formal_skeleton": EpistemicStatus.FORMALIZED_INCOMPLETE,
        }
        return mapping[value]

    @staticmethod
    def _invariants(address: FrontierAddress) -> tuple[str, ...]:
        c = address.as_mapping()
        invariants = [
            "dimension compatibility",
            "basis covariance",
            "residual preservation",
        ]
        if c["geometry"] in {"euclidean", "hermitian", "riemannian"}:
            invariants.append("metric consistency")
        if c["operator"] in {"incidence", "laplacian", "cross_scale"}:
            invariants.extend(("boundary consistency", "conservation audit"))
        if c["regime"] == "stochastic":
            invariants.append("probability normalization")
        if c["scalar"] in {"octonion_guarded", "sedenion_exploratory"}:
            invariants.append("parenthesization provenance")
        return tuple(invariants)

    @staticmethod
    def _baselines(address: FrontierAddress) -> tuple[str, ...]:
        c = address.as_mapping()
        values = ["dense reference implementation", "known limiting case"]
        if c["discretization"] != "exact_symbolic":
            values.append("mesh or resolution refinement")
        if c["operator"] in {"matrix", "projection", "laplacian"}:
            values.append("NumPy/SciPy linear algebra")
        if c["space"] in {"graph_chain", "simplicial_chain", "hypergraph_chain"}:
            values.append("classical graph or simplicial operator")
        if c["application"] != "pure_mathematics":
            values.append(f"domain baseline for {c['application']}")
        return tuple(values)

    @staticmethod
    def _falsifiers(address: FrontierAddress) -> tuple[str, ...]:
        c = address.as_mapping()
        falsifiers = [
            "dimension mismatch",
            "singular or near-singular fixture",
            "random small-model counterexample search",
            "change-of-basis inconsistency",
            "structured residual above declared tolerance",
        ]
        if c["regime"] in {"singular", "strongly_nonlinear"}:
            falsifiers.append("local-to-global extrapolation failure")
        if c["scalar"] == "sedenion_exploratory":
            falsifiers.extend(("zero-divisor sector", "parenthesization dependence"))
        if c["method"] == "formal_assistant":
            falsifiers.append("unresolved formal placeholder")
        return tuple(falsifiers)

    @staticmethod
    def _expected_artifacts(method: str, question: str) -> tuple[str, ...]:
        artifacts = ["problem-card.json", "oak-report.json", "reproduction.md"]
        if method == "formal_assistant":
            artifacts.append("formal-target")
        if method in {"numerical_falsification", "interval_arithmetic"}:
            artifacts.extend(("fixture.json", "certificate.json"))
        if question == "counterexample":
            artifacts.append("minimal-counterexample.json")
        else:
            artifacts.append("proof-or-disproof-plan.md")
        return tuple(artifacts)

    @staticmethod
    def _scores(address: FrontierAddress) -> tuple[float, float, float, float]:
        digest = sha256(address.canonical().encode("utf-8")).digest()
        raw = [byte / 255.0 for byte in digest[:4]]
        priority = 0.25 + 0.75 * raw[0]
        novelty = 0.15 + 0.85 * raw[1]
        testability = 0.30 + 0.70 * raw[2]
        risk = 0.05 + 0.75 * raw[3]
        c = address.as_mapping()
        if c["method"] in {"interval_arithmetic", "formal_assistant"}:
            testability = min(1.0, testability + 0.1)
        if c["scalar"] in {"octonion_guarded", "sedenion_exploratory"}:
            risk = min(1.0, risk + 0.2)
        return priority, novelty, testability, risk
