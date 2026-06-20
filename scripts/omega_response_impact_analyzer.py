#!/usr/bin/env python3
"""
Omega Response Impact Analyzer.

Quantifies the impact of a response or iteration by scoring concrete artifacts,
diversity, OAK safety, automation, tests, strategic leverage, and reuse.

Boundary:
- Scores are operational heuristics, not truth or scientific validation.
- The analyzer rewards reviewable, bounded, testable changes.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_AXES = {
    "version": "omega.response_impact_axes.v1",
    "max_score": 100,
    "axes": [
        {"key": "artifact_count", "weight": 18},
        {"key": "diversity", "weight": 16},
        {"key": "oak_safety", "weight": 16},
        {"key": "automation", "weight": 14},
        {"key": "testability", "weight": 14},
        {"key": "strategic_value", "weight": 12},
        {"key": "reuse", "weight": 10},
    ],
}

CATEGORY_BY_PREFIX = {
    "scripts/": "code",
    "tests/": "tests",
    ".github/workflows/": "workflow",
    "docs/": "docs",
    "ops/": "ops",
    "configs/": "config",
    "schemas/": "schema",
    "interfaces/": "interface",
    "artifacts/": "artifact",
}

STRATEGIC_MARKERS = [
    "chatgpt",
    "iteration",
    "multiplier",
    "oak",
    "hgfm",
    "publication",
    "data",
    "spectro",
    "bayes",
    "ait",
    "workflow",
]

OAK_MARKERS = ["oak", "bounded", "review", "prototype", "proof", "license", "residue", "human"]


@dataclass
class ImpactInput:
    artifacts: List[str]
    summary: str = ""
    tests: List[str] = None
    workflows: List[str] = None
    residues: List[str] = None

    def __post_init__(self) -> None:
        self.tests = self.tests or []
        self.workflows = self.workflows or []
        self.residues = self.residues or []


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def category(path: str) -> str:
    for prefix, cat in CATEGORY_BY_PREFIX.items():
        if path.startswith(prefix):
            return cat
    return "other"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_input(data: ImpactInput, axes: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = data.artifacts
    text = " ".join(artifacts + [data.summary] + data.tests + data.workflows + data.residues).lower()
    categories = sorted({category(path) for path in artifacts})
    axis_raw = {
        "artifact_count": clamp01(len(artifacts) / 12.0),
        "diversity": clamp01(len(categories) / 8.0),
        "oak_safety": clamp01(sum(1 for marker in OAK_MARKERS if marker in text) / len(OAK_MARKERS)),
        "automation": clamp01((len(data.workflows) + sum(1 for a in artifacts if a.startswith("scripts/") or a.startswith(".github/workflows/"))) / 4.0),
        "testability": clamp01((len(data.tests) + sum(1 for a in artifacts if a.startswith("tests/") or "validator" in a)) / 4.0),
        "strategic_value": clamp01(sum(1 for marker in STRATEGIC_MARKERS if marker in text) / 7.0),
        "reuse": clamp01(sum(1 for a in artifacts if a.startswith("configs/") or a.startswith("schemas/") or "example" in a or "template" in a or "manifest" in a) / 5.0),
    }
    weighted: Dict[str, float] = {}
    total = 0.0
    for axis in axes.get("axes", DEFAULT_AXES["axes"]):
        key = axis["key"]
        weight = float(axis["weight"])
        value = axis_raw.get(key, 0.0) * weight
        weighted[key] = round(value, 2)
        total += value
    score = round(total, 2)
    rating = "plus_ultra" if score >= 81 else "very_strong" if score >= 61 else "strong" if score >= 41 else "useful" if score >= 21 else "weak"
    return {
        "version": "omega.response_impact_report.v1",
        "score": score,
        "max_score": axes.get("max_score", 100),
        "rating": rating,
        "axis_scores": weighted,
        "artifact_count": len(artifacts),
        "categories": categories,
        "tests_count": len(data.tests),
        "workflow_count": len(data.workflows),
        "residue_count": len(data.residues),
        "oak_boundary": {
            "heuristic_score_only": True,
            "not_scientific_validation": True,
            "human_review_for_external_action": True,
        },
    }


def read_input(path: Path) -> ImpactInput:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ImpactInput(
        artifacts=list(raw.get("artifacts", [])),
        summary=raw.get("summary", ""),
        tests=list(raw.get("tests", [])),
        workflows=list(raw.get("workflows", [])),
        residues=list(raw.get("residues", [])),
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a Tristan response/iteration impact report.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--axes", default="configs/omega_response_impact_axes.json")
    parser.add_argument("--out", default="artifacts/response_impact_report.json")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    axes = load_json(Path(args.axes), DEFAULT_AXES)
    data = read_input(Path(args.input))
    report = score_input(data, axes)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
