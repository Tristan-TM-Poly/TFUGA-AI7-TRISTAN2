from __future__ import annotations


def compare_scores(current: dict[str, object], baseline: dict[str, object]) -> dict[str, object]:
    current_total = int(current.get("total", 0))
    baseline_total = int(baseline.get("total", 0))
    current_pass_rate = float(current.get("pass_rate", 0.0))
    baseline_pass_rate = float(baseline.get("pass_rate", 0.0))
    workflows_preserved = current_total >= baseline_total
    pass_rate_preserved = current_pass_rate >= baseline_pass_rate
    return {
        "current_total": current_total,
        "baseline_total": baseline_total,
        "current_pass_rate": current_pass_rate,
        "baseline_pass_rate": baseline_pass_rate,
        "workflows_preserved": workflows_preserved,
        "pass_rate_preserved": pass_rate_preserved,
        "passed": workflows_preserved and pass_rate_preserved,
    }
