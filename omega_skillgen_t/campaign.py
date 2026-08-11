from __future__ import annotations

from pathlib import Path
import copy
import json
from typing import Any

from .core import generate_skill, lint_skill, eval_coverage, validate_spec
from .trust import scan_skill_trust
from .meta import mutate_spec, compare_specs

DEFAULT_STRATEGIES = ("activation-precision", "oak-hardening", "eval-hardening")


def _complexity(spec: dict[str, Any]) -> dict[str, int]:
    return {
        "description_chars": len(str(spec.get("description", ""))),
        "workflow_steps": len(spec.get("workflow", [])),
        "invariants": len(spec.get("invariants", [])),
        "eval_cases": len(spec.get("eval_cases", [])),
        "json_chars": len(json.dumps(spec, ensure_ascii=False)),
    }


def _static_score(lint, coverage, trust, complexity) -> float:
    """Heuristic static score only; never behavioral fitness."""
    score = 0.0
    score += 4.0 if lint["status"] == "PASS" else -8.0
    score += 4.0 if coverage["status"] == "PASS" else -8.0
    score += {"PASS": 3.0, "PASS_WITH_FINDINGS": 1.0, "REVIEW": -5.0}.get(trust["status"], -2.0)
    score -= 0.001 * complexity["json_chars"]
    return round(score, 6)


def run_static_campaign(spec: dict[str, Any], out_dir: str | Path, strategies=DEFAULT_STRATEGIES) -> dict[str, Any]:
    out = Path(out_dir)
    if out.exists():
        import shutil
        shutil.rmtree(out)
    (out / "specs").mkdir(parents=True)
    (out / "skills").mkdir()

    candidates = [("parent", copy.deepcopy(spec))]
    for strategy in strategies:
        candidates.append((strategy, mutate_spec(spec, strategy)))
    combined = copy.deepcopy(spec)
    for strategy in strategies:
        combined = mutate_spec(combined, strategy)
    candidates.append(("combined", combined))

    results = []
    for label, candidate in candidates:
        errors = validate_spec(candidate)
        if errors:
            results.append({"label": label, "status": "INVALID_SPEC", "errors": errors})
            continue
        (out / "specs" / f"{label}.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        skill_dir = generate_skill(candidate, out / "skills" / label)
        lint = lint_skill(skill_dir)
        coverage = eval_coverage(skill_dir)
        trust = scan_skill_trust(skill_dir)
        complexity = _complexity(candidate)
        results.append({
            "label": label,
            "status": "STATIC_CANDIDATE",
            "lint": lint["status"],
            "eval_coverage": coverage["status"],
            "trust": trust["status"],
            "trust_findings": trust["finding_count"],
            "complexity": complexity,
            "heuristic_static_score": _static_score(lint, coverage, trust, complexity),
            "delta_from_parent": compare_specs(spec, candidate),
        })

    ranked = sorted(
        [r for r in results if r.get("status") == "STATIC_CANDIDATE"],
        key=lambda r: (-r["heuristic_static_score"], r["complexity"]["json_chars"], r["label"]),
    )
    report = {
        "campaign_status": "STATIC_ONLY",
        "behavioral_runtime_eval": "NOT_RUN",
        "auto_promotion": False,
        "strategies": list(strategies),
        "results": results,
        "static_ranking": [r["label"] for r in ranked],
        "best_static_candidate": ranked[0]["label"] if ranked else None,
        "promotion_rule": "Ranking is heuristic evidence for review, never automatic promotion.",
    }
    (out / "CAMPAIGN_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
