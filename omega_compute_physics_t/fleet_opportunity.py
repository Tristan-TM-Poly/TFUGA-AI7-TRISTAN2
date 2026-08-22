"""Bridge R0.6 RepositoryGenome/CallGraph evidence into R0.7 opportunities."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .call_graph import CallGraphReport
from .opportunity_engine import OpportunityDecision, OpportunityEvidence, rank_optimization_opportunities
from .repo_scanner import FunctionGenome, RepositoryGenome


@dataclass(frozen=True)
class FleetOpportunityReport:
    repository: str
    evidence: tuple[OpportunityEvidence, ...]
    decisions: tuple[OpportunityDecision, ...]
    status: str = "static-fleet-optimization-opportunities"
    oak_warning: str = (
        "This report compiles static structure, partial call-graph centrality and "
        "supplied priors into experiment priorities. It does not prove runtime "
        "hotspots, bottlenecks, feasible optimizations or speedups."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "evidence": [asdict(row) for row in self.evidence],
            "decisions": [row.to_dict() for row in self.decisions],
            "status": self.status,
            "oak_warning": self.oak_warning,
        }


def _static_complexity(function: FunctionGenome) -> float:
    return (
        2.0 * function.max_loop_depth
        + 0.5 * function.loops
        + 0.25 * function.branches
        + 0.10 * function.calls
        + 0.25 * function.allocations
        + 0.10 * function.comprehensions
        + 1.0 * float(function.direct_recursion)
        + 0.02 * function.loc
    )


def compile_fleet_opportunities(
    repository: str,
    genome: RepositoryGenome,
    call_graph: CallGraphReport,
    *,
    regression_signals: Mapping[str, float] | None = None,
    confidence_debts: Mapping[str, float] | None = None,
    usage_weights: Mapping[str, float] | None = None,
    expected_savings_priors: Mapping[str, float] | None = None,
    engineering_effort_hours: Mapping[str, float] | None = None,
    benchmark_costs: Mapping[str, float] | None = None,
) -> FleetOpportunityReport:
    regression_signals = regression_signals or {}
    confidence_debts = confidence_debts or {}
    usage_weights = usage_weights or {}
    expected_savings_priors = expected_savings_priors or {}
    engineering_effort_hours = engineering_effort_hours or {}
    benchmark_costs = benchmark_costs or {}

    evidence: list[OpportunityEvidence] = []
    for module in genome.modules:
        for function in module.functions:
            node = f"{function.module}:{function.qualified_name}"
            centrality = float(call_graph.fan_in.get(node, 0) + call_graph.fan_out.get(node, 0))
            evidence.append(
                OpportunityEvidence(
                    repository=repository,
                    node=node,
                    static_complexity=_static_complexity(function),
                    graph_centrality=centrality,
                    usage_weight=float(usage_weights.get(node, 1.0)),
                    regression_signal=float(regression_signals.get(node, 0.0)),
                    expected_savings_prior=float(expected_savings_priors.get(node, 0.10)),
                    confidence_debt=float(confidence_debts.get(node, 0.50)),
                    engineering_effort_hours=float(engineering_effort_hours.get(node, 1.0)),
                    benchmark_cost=float(benchmark_costs.get(node, 1.0)),
                    evidence_note="static R0.6->R0.7 compiled opportunity",
                )
            )
    rows = tuple(evidence)
    return FleetOpportunityReport(
        repository=repository,
        evidence=rows,
        decisions=rank_optimization_opportunities(rows),
    )
