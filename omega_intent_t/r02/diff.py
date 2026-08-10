from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class MetricRule:
    direction: str
    weight: float = 1.0


DEFAULT_RULES: dict[str, MetricRule] = {
    "validated": MetricRule("up", 2.0),
    "tests_passed": MetricRule("up", 3.0),
    "coverage": MetricRule("up", 2.0),
    "benchmark_wins": MetricRule("up", 2.0),
    "open_residuals": MetricRule("down", 1.5),
    "critical_risks_open": MetricRule("down", 4.0),
    "benchmark_regressions": MetricRule("down", 2.5),
    "failure_rate": MetricRule("down", 2.0),
    "artifact_bytes": MetricRule("neutral", 0.0),
    "additions": MetricRule("neutral", 0.0),
}


def compare_reports(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    rules: Mapping[str, MetricRule] | None = None,
) -> dict[str, Any]:
    selected = dict(DEFAULT_RULES)
    if rules:
        selected.update(rules)
    metrics: list[dict[str, Any]] = []
    score = 0.0
    regressions = 0
    improvements = 0
    for name, rule in sorted(selected.items()):
        if name not in before or name not in after:
            continue
        old = before[name]
        new = after[name]
        if not isinstance(old, (int, float, bool)) or not isinstance(new, (int, float, bool)):
            continue
        delta = float(new) - float(old)
        if rule.direction == "up":
            contribution = delta * rule.weight
        elif rule.direction == "down":
            contribution = -delta * rule.weight
        else:
            contribution = 0.0
        classification = "neutral"
        if contribution > 0:
            classification = "improvement"
            improvements += 1
        elif contribution < 0:
            classification = "regression"
            regressions += 1
        score += contribution
        metrics.append(
            {
                "metric": name,
                "before": old,
                "after": new,
                "delta": delta,
                "direction": rule.direction,
                "weight": rule.weight,
                "contribution": contribution,
                "classification": classification,
            }
        )
    if regressions:
        status = "regressed"
    elif improvements:
        status = "improved"
    else:
        status = "unchanged"
    return {
        "schema": "omega-intent-report-diff/v2",
        "status": status,
        "score": score,
        "improvements": improvements,
        "regressions": regressions,
        "metrics": metrics,
        "volume_metrics_have_final_authority": False,
    }
