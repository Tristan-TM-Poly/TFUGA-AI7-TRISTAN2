#!/usr/bin/env python3
"""Select a diverse high-value batch from Omega Iteration Multiplier candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG = {
    "version": "omega.iteration_batch_selector.config.v1",
    "default_batch_size": 16,
    "priority_weight": 0.45,
    "diversity_weight": 0.35,
    "oak_weight": 0.20,
    "preferred_actions": ["add_validator", "add_test", "add_workflow", "add_schema", "add_runbook", "add_dashboard", "add_safety_check", "add_benchmark_plan"],
}


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def novelty(candidate: Dict[str, Any], selected: List[Dict[str, Any]]) -> float:
    if not selected:
        return 1.0
    score = 0.0
    for key in ["layer", "module", "action"]:
        used = {item.get(key) for item in selected}
        if candidate.get(key) not in used:
            score += 1.0 / 3.0
    return score


def oak_score(candidate: Dict[str, Any]) -> float:
    gates = candidate.get("oak_gates", []) or []
    residues = candidate.get("residues", []) or []
    return min(1.0, (len(gates) / 6.0) + (0.05 if residues else 0.0))


def candidate_score(candidate: Dict[str, Any], selected: List[Dict[str, Any]], cfg: Dict[str, Any]) -> float:
    priority = float(candidate.get("priority", 0)) / 100.0
    preferred = 0.15 if candidate.get("action") in set(cfg.get("preferred_actions", [])) else 0.0
    return (
        cfg.get("priority_weight", 0.45) * priority
        + cfg.get("diversity_weight", 0.35) * novelty(candidate, selected)
        + cfg.get("oak_weight", 0.20) * oak_score(candidate)
        + preferred
    )


def select_batch(candidates: List[Dict[str, Any]], batch_size: int, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    remaining = list(candidates)
    selected: List[Dict[str, Any]] = []
    while remaining and len(selected) < batch_size:
        best = max(remaining, key=lambda item: candidate_score(item, selected, cfg))
        selected.append(best)
        remaining.remove(best)
    return selected


def summarize(selected: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "count": len(selected),
        "layers": sorted({item.get("layer") for item in selected}),
        "modules": sorted({item.get("module") for item in selected}),
        "actions": sorted({item.get("action") for item in selected}),
        "avg_priority": round(sum(float(item.get("priority", 0)) for item in selected) / max(1, len(selected)), 2),
    }


def write_outputs(selected: List[Dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(selected)
    report = {
        "version": "omega.iteration_selected_batch.v1",
        "summary": summary,
        "selected": selected,
        "oak_boundary": {
            "bounded_batch": True,
            "selected_not_all_candidates": True,
            "human_review_required": True,
        },
    }
    (out_dir / "selected_batch.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Selected Omega Iteration Batch", "", f"Count: {summary['count']}", f"Average priority: {summary['avg_priority']}", "", "## Candidates"]
    for item in selected:
        lines.append(f"- `{item.get('id')}` {item.get('title')} files={', '.join(item.get('files', []))}")
    (out_dir / "selected_batch_prompt.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select a diverse batch from iteration multiplier candidates.")
    parser.add_argument("--manifest", default="artifacts/iteration_multiplier/iteration_multiplier_manifest.json")
    parser.add_argument("--config", default="configs/omega_iteration_multiplier_batch_selector.json")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--out-dir", default="artifacts/iteration_selected_batch")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    manifest = load_json(Path(args.manifest), {"additions": []})
    cfg = load_json(Path(args.config), DEFAULT_CONFIG)
    selected = select_batch(manifest.get("additions", []), args.batch_size, cfg)
    write_outputs(selected, Path(args.out_dir))
    print(json.dumps(summarize(selected), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
