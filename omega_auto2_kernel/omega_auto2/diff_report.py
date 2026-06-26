from __future__ import annotations

import json

from .regression import current_canonical_suite
from .score_compare import compare_scores


def build_diff_payload(baseline: dict[str, object] | None = None) -> dict[str, object]:
    current = current_canonical_suite()
    if baseline and "suite" in baseline:
        baseline_suite = baseline["suite"]
    else:
        baseline_suite = baseline or {"total": 4, "pass_rate": 0.0, "results": []}
    comparison = compare_scores(current, baseline_suite)
    return {
        "kind": "auto2_benchmark_diff",
        "current": current,
        "baseline": baseline_suite,
        "comparison": comparison,
        "passed": comparison["passed"],
    }


def diff_json(baseline: dict[str, object] | None = None) -> str:
    return json.dumps(build_diff_payload(baseline), ensure_ascii=False, indent=2, sort_keys=True)


def diff_markdown(baseline: dict[str, object] | None = None) -> str:
    payload = build_diff_payload(baseline)
    comp = payload["comparison"]
    lines = [
        "# Ω-AUTO² Benchmark Diff",
        "",
        f"Passed: {payload['passed']}",
        "",
        "| Metric | Baseline | Current | Preserved |",
        "|---|---:|---:|---:|",
        f"| Workflows | {comp['baseline_total']} | {comp['current_total']} | {comp['workflows_preserved']} |",
        f"| Pass rate | {comp['baseline_pass_rate']} | {comp['current_pass_rate']} | {comp['pass_rate_preserved']} |",
        "",
        "OAK note: diff reports are local text outputs only.",
    ]
    return "\n".join(lines)
