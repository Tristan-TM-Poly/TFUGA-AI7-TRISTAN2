"""R0.6.1 cumulative coalition-risk gate for the Tensor Research Compiler.

R0.6 originally enforced `ProblemGenome.risk_budget` per candidate LLMT.  That
is insufficient for a coalition: several individually admissible members can
exceed the portfolio budget when combined.  This module provides a fail-closed
wrapper compiler whose selection loop constrains cumulative risk.

Risk values remain declared software-policy proxies.  Passing this gate does
not establish real-world safety, optimal risk allocation, or independence of
risk factors.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
from typing import Sequence

from sage_tristan.tensor_research_compiler import (
    LLMTMarginal,
    LLMTRegistry,
    PersonLLMT,
    ProblemGenome,
    SparseTensorCoalitionCompiler,
    synthetic_tensor_fixture,
)


@dataclass(frozen=True, slots=True)
class CumulativeRiskCoalitionReceipt:
    problem_id: str
    selected_person_ids: tuple[str, ...]
    rejected_person_ids: tuple[str, ...]
    covered_capabilities: tuple[str, ...]
    uncovered_capabilities: tuple[str, ...]
    marginals: tuple[LLMTMarginal, ...]
    cumulative_risk: float
    risk_budget: float
    cumulative_risk_within_budget: bool
    stop_reason: str
    risk_aggregation_model: str = "additive_declared_proxy"
    portfolio_risk_optimality_proven: bool = False
    risk_independence_assumed: bool = False
    full_tensor_materialized: bool = False


@dataclass(frozen=True, slots=True)
class CumulativeRiskTensorCompiler:
    registry: LLMTRegistry

    def compile(
        self,
        problem: ProblemGenome,
        *,
        max_llmts: int = 4,
        min_marginal_gain: float = 0.05,
    ) -> CumulativeRiskCoalitionReceipt:
        if max_llmts < 1:
            raise ValueError("max_llmts must be >= 1")

        selected: list[PersonLLMT] = []
        available = list(self.registry.llmts)
        covered: frozenset[str] = frozenset()
        marginals: list[LLMTMarginal] = []
        required = set(problem.capability_tags)
        cumulative_risk = 0.0
        stop_reason = "no_positive_marginal_gain"

        while available and len(selected) < max_llmts and set(covered) != required:
            risk_admissible = [
                item
                for item in available
                if cumulative_risk + item.risk <= problem.risk_budget + 1e-12
            ]
            if not risk_admissible:
                stop_reason = "cumulative_risk_budget_exhausted"
                break

            scored = [
                SparseTensorCoalitionCompiler._marginal(problem, item, covered, selected)
                for item in risk_admissible
            ]
            scored.sort(key=lambda item: (-item.marginal_gain, item.person_id))
            best = scored[0]
            if best.marginal_gain < min_marginal_gain:
                stop_reason = "marginal_gain_below_threshold"
                break

            llmt = self.registry.get(best.person_id)
            selected.append(llmt)
            available = [item for item in available if item.person_id != llmt.person_id]
            covered = frozenset(set(covered) | (set(llmt.capability_tags) & required))
            cumulative_risk += llmt.risk
            marginals.append(best)
            if set(covered) == required:
                stop_reason = "required_capabilities_covered"
                break
        else:
            if len(selected) >= max_llmts and set(covered) != required:
                stop_reason = "max_llmts_reached"

        selected_ids = tuple(item.person_id for item in selected)
        rejected_ids = tuple(sorted(item.person_id for item in self.registry.llmts if item.person_id not in selected_ids))
        cumulative_risk = round(cumulative_risk, 6)
        return CumulativeRiskCoalitionReceipt(
            problem_id=problem.problem_id,
            selected_person_ids=selected_ids,
            rejected_person_ids=rejected_ids,
            covered_capabilities=tuple(sorted(covered)),
            uncovered_capabilities=tuple(sorted(required - set(covered))),
            marginals=tuple(marginals),
            cumulative_risk=cumulative_risk,
            risk_budget=problem.risk_budget,
            cumulative_risk_within_budget=cumulative_risk <= problem.risk_budget + 1e-12,
            stop_reason=stop_reason,
        )


def synthetic_cumulative_risk_fixture() -> tuple[LLMTRegistry, ProblemGenome]:
    """Two candidates pass individually but cannot coexist under the budget."""
    registry = LLMTRegistry(
        (
            PersonLLMT(
                "risk_a", "synthetic-v1", ("ca",), ("sa",), ("op_a",), ("ra",), ("cap_a",),
                cost=0.1, risk=0.30,
            ),
            PersonLLMT(
                "risk_b", "synthetic-v1", ("cb",), ("sb",), ("op_b",), ("rb",), ("cap_b",),
                cost=0.1, risk=0.30,
            ),
        )
    )
    problem = ProblemGenome(
        "cumulative_risk_fixture",
        ("cap_a", "cap_b"),
        ("risk",),
        ("ra",),
        ("rb",),
        risk_budget=0.50,
    )
    return registry, problem


def compile_report() -> dict[str, object]:
    standard_registry, standard_problem = synthetic_tensor_fixture()
    standard = CumulativeRiskTensorCompiler(standard_registry).compile(standard_problem, max_llmts=3)
    risk_registry, risk_problem = synthetic_cumulative_risk_fixture()
    constrained = CumulativeRiskTensorCompiler(risk_registry).compile(risk_problem, max_llmts=2)
    return {
        "engine": "Omega-TENSOR-RISK-GATE-T",
        "release": "R0.6.1",
        "standard_fixture": asdict(standard),
        "cumulative_risk_fixture": asdict(constrained),
        "per_agent_risk_is_coalition_risk": False,
        "cumulative_risk_gate_present": True,
        "risk_aggregation_model": "additive_declared_proxy",
        "portfolio_risk_optimality_proven": False,
        "risk_independence_assumed": False,
        "real_world_safety_certified": False,
        "oak_note": (
            "The additive cumulative-risk gate closes the R0.6 per-agent budget loophole for declared proxy risk. "
            "It does not model correlated real-world hazards or prove portfolio-risk optimality."
        ),
    }


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "value"):
        return value.value
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Tensor cumulative coalition-risk gate R0.6.1")
    parser.add_argument("--report", action="store_true")
    parser.parse_args(argv)
    print(json.dumps(_jsonable(compile_report()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
