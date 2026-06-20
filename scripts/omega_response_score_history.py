#!/usr/bin/env python3
"""Build a quantitative history dashboard from response impact inputs or reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


RATING_ORDER = ["weak", "useful", "strong", "very_strong", "plus_ultra"]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_score(record: Dict[str, Any]) -> float:
    if "score" in record:
        return float(record.get("score", 0))
    artifacts = len(record.get("artifacts", []))
    tests = len(record.get("tests", []))
    workflows = len(record.get("workflows", []))
    residues = len(record.get("residues", []))
    score = min(100.0, artifacts * 5.0 + tests * 3.0 + workflows * 6.0 + min(10, residues * 1.0))
    return round(score, 2)


def rating(score: float) -> str:
    if score >= 81:
        return "plus_ultra"
    if score >= 61:
        return "very_strong"
    if score >= 41:
        return "strong"
    if score >= 21:
        return "useful"
    return "weak"


def normalize(path: Path) -> Dict[str, Any]:
    raw = load_json(path)
    score = infer_score(raw)
    return {
        "source": str(path),
        "summary": raw.get("summary", raw.get("version", path.stem)),
        "score": score,
        "rating": raw.get("rating", rating(score)),
        "artifact_count": raw.get("artifact_count", len(raw.get("artifacts", []))),
        "tests_count": raw.get("tests_count", len(raw.get("tests", []))),
        "workflow_count": raw.get("workflow_count", len(raw.get("workflows", []))),
        "residue_count": raw.get("residue_count", len(raw.get("residues", []))),
    }


def collect(inputs_dir: Path) -> List[Dict[str, Any]]:
    records = []
    for path in sorted(inputs_dir.glob("*.json")):
        records.append(normalize(path))
    return records


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {"count": 0, "avg_score": 0, "best_score": 0, "latest_score": 0, "trend": 0}
    scores = [float(r["score"]) for r in records]
    return {
        "count": len(records),
        "avg_score": round(sum(scores) / len(scores), 2),
        "best_score": round(max(scores), 2),
        "latest_score": round(scores[-1], 2),
        "trend": round(scores[-1] - scores[0], 2),
        "plus_ultra_count": sum(1 for score in scores if score >= 81),
    }


def write_outputs(records: List[Dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(records)
    payload = {
        "version": "omega.response_score_history.v1",
        "summary": summary,
        "records": records,
        "oak_boundary": {
            "scores_are_heuristics": True,
            "not_scientific_validation": True,
            "trend_is_process_signal": True,
        },
    }
    (out_dir / "response_score_history.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Omega Response Score History", "", f"Responses: {summary['count']}", f"Average score: {summary['avg_score']}", f"Best score: {summary['best_score']}", f"Latest score: {summary['latest_score']}", f"Trend: {summary['trend']}", "", "## Records"]
    for idx, record in enumerate(records, start=1):
        lines.append(f"{idx}. **{record['rating']}** `{record['score']}` — {record['summary']}")
    lines.extend(["", "## OAK boundary", "Scores are process heuristics, not proof or scientific validation."])
    (out_dir / "RESPONSE_SCORE_HISTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build response impact score history dashboard.")
    parser.add_argument("--inputs-dir", default="configs/response_impact")
    parser.add_argument("--out-dir", default="artifacts/response_score_history")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    records = collect(Path(args.inputs_dir))
    write_outputs(records, Path(args.out_dir))
    print(json.dumps(summarize(records), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
