from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .hashing import sha256_hex, stable_id
from .models import AttemptStatus, ResolutionReceipt


@dataclass(frozen=True)
class ProblemResolutionInsight:
    insight_id: str
    rank: int
    kind: str
    subject: str
    score: float
    evidence: tuple[str, ...]
    conclusion: str
    next_experiment: str
    falsifier: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "rank": self.rank,
            "kind": self.kind,
            "subject": self.subject,
            "score": self.score,
            "evidence": list(self.evidence),
            "conclusion": self.conclusion,
            "next_experiment": self.next_experiment,
            "falsifier": self.falsifier,
        }


class ResolutionAnalyzer:
    def analyze(self, receipt: ResolutionReceipt, *, limit: int = 12) -> dict[str, Any]:
        failed_by_strategy: Counter[str] = Counter()
        counterexamples_by_strategy: dict[str, set[str]] = defaultdict(set)
        selected_by_strategy: Counter[str] = Counter()
        for record in receipt.records:
            if record.selected_strategy_id:
                selected_by_strategy[record.selected_strategy_id] += 1
            for attempt in record.attempts:
                if attempt.status is not AttemptStatus.VERIFIED:
                    failed_by_strategy[attempt.strategy_id] += 1
                    if attempt.counterexample_signature:
                        counterexamples_by_strategy[attempt.strategy_id].add(
                            attempt.counterexample_signature
                        )

        raw: list[tuple[float, str, str, tuple[str, ...], str, str, str]] = []
        for metric in receipt.family_metrics:
            fallback_rate = metric.fallback_solves / metric.attempted if metric.attempted else 0.0
            score = fallback_rate * 3.0 + metric.attempts_per_solve
            raw.append(
                (
                    score,
                    "family_bottleneck",
                    metric.family_id,
                    (
                        f"attempted={metric.attempted}",
                        f"fallback_solves={metric.fallback_solves}",
                        f"counterexamples={metric.counterexamples}",
                        f"attempts_per_solve={metric.attempts_per_solve:.6f}",
                    ),
                    "The family is solvable by the current exact portfolio, but fragile heuristics create informative failures.",
                    "Generate adversarial variants concentrated around the heuristic assumptions and rerun both strategies.",
                    "The conclusion is weakened if independent variants no longer require fallback strategies.",
                )
            )
        for strategy_id, failures in failed_by_strategy.items():
            unique = len(counterexamples_by_strategy[strategy_id])
            score = failures + unique * 0.5
            raw.append(
                (
                    score,
                    "strategy_failure",
                    strategy_id,
                    (
                        f"failed_attempts={failures}",
                        f"unique_counterexamples={unique}",
                        f"selected_successes={selected_by_strategy[strategy_id]}",
                    ),
                    "The strategy assumptions are too weak for the observed input distribution.",
                    "Minimize one counterexample per failure mode and convert it into a permanent regression property.",
                    "The conclusion is falsified if the same strategy passes a broader independently generated distribution without changing its assumptions.",
                )
            )

        raw.sort(key=lambda item: (-item[0], item[1], item[2]))
        insights = []
        for rank, item in enumerate(raw[:limit], start=1):
            score, kind, subject, evidence, conclusion, experiment, falsifier = item
            insights.append(
                ProblemResolutionInsight(
                    insight_id=stable_id(
                        "resolution-insight",
                        {"kind": kind, "subject": subject, "evidence": evidence},
                        length=20,
                    ),
                    rank=rank,
                    kind=kind,
                    subject=subject,
                    score=score,
                    evidence=evidence,
                    conclusion=conclusion,
                    next_experiment=experiment,
                    falsifier=falsifier,
                )
            )
        report = {
            "system": "omega-code-dojo-t-infinity",
            "version": "R0.4",
            "campaign_id": receipt.campaign_id,
            "logical_problem_space": receipt.logical_problem_space,
            "materialized_problems": receipt.materialized_problems,
            "solved_problems": receipt.solved_problems,
            "unresolved_problems": receipt.unresolved_problems,
            "solve_rate": receipt.solve_rate,
            "fallback_solutions": sum(metric.fallback_solves for metric in receipt.family_metrics),
            "unique_counterexamples": len(
                {
                    attempt.counterexample_signature
                    for record in receipt.records
                    for attempt in record.attempts
                    if attempt.counterexample_signature
                }
            ),
            "insights": [insight.to_dict() for insight in insights],
            "claims": {
                "maximum_problem_resolution_claimed": False,
                "finite_portfolio_resolution_measured": True,
                "open_problem_solution_claimed": False,
                "generalization_claimed": False,
            },
        }
        report["report_sha256"] = sha256_hex(report)
        return report
