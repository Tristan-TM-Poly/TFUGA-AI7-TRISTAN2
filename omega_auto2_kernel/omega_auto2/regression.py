from __future__ import annotations

import json
from pathlib import Path

from .canonical import canonical_workflows
from .exporters import suite_json
from .score_compare import compare_scores


def current_canonical_suite() -> dict[str, object]:
    return json.loads(suite_json(canonical_workflows()))


def load_baseline(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def regression_check(baseline: dict[str, object] | None = None) -> dict[str, object]:
    current = current_canonical_suite()
    baseline = baseline or {
        "total": 4,
        "passed": 0,
        "failed": 4,
        "pass_rate": 0.0,
        "results": [],
    }
    comparison = compare_scores(current, baseline)
    return {
        "current": current,
        "baseline": baseline,
        "comparison": comparison,
        "passed": comparison["passed"],
    }
