"""Strict audit extension for Ω-PROBLEM-ATLAS-T∞ R0.3 MAX."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .atlas import ATTACK_MODES, stable_digest
from .max_engine import METHOD_FAMILIES, TARGET_KINDS, _read_jsonl, audit_max_output


EXPECTED_ARTIFACTS = {
    "sources.jsonl",
    "problems.jsonl",
    "research_targets.jsonl",
    "research_cells.jsonl",
    "hyperedges.jsonl",
    "methods.jsonl",
    "portfolio.json",
}


def audit_max_output_strict(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    base = audit_max_output(output)
    errors = list(base["errors"])
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    portfolio = json.loads((output / "portfolio.json").read_text(encoding="utf-8"))
    problems = _read_jsonl(output / "problems.jsonl")
    targets = _read_jsonl(output / "research_targets.jsonl")
    cells = _read_jsonl(output / "research_cells.jsonl")
    edges = _read_jsonl(output / "hyperedges.jsonl")
    methods = _read_jsonl(output / "methods.jsonl")

    claimed_report_digest = report.get("digest")
    report_without_digest = dict(report)
    report_without_digest.pop("digest", None)
    if claimed_report_digest != stable_digest(report_without_digest):
        errors.append("report digest mismatch")

    artifact_names = {item.get("path") for item in manifest.get("artifacts", [])}
    if artifact_names != EXPECTED_ARTIFACTS:
        errors.append(
            "manifest artifact contract mismatch: "
            f"expected {sorted(EXPECTED_ARTIFACTS)}, got {sorted(str(x) for x in artifact_names)}"
        )

    problem_ids = {row["problem_id"] for row in problems}
    canonical_keys = [row["canonical_key"] for row in problems]
    target_ids = {row["target_id"] for row in targets}
    cell_ids = {row["cell_id"] for row in cells}
    method_ids = {row["method_id"] for row in methods}
    known_nodes = problem_ids | target_ids | cell_ids | method_ids | set(ATTACK_MODES)

    if len(canonical_keys) != len(set(canonical_keys)):
        errors.append("duplicate problem canonical keys")
    if len(targets) != len(problems) * len(TARGET_KINDS):
        errors.append("research target cardinality is not problems × target kinds")
    if len(cells) != len(targets) * len(ATTACK_MODES):
        errors.append("research cell cardinality is not targets × attack modes")
    expected_edge_count = len(targets) + (len(targets) - len(problems)) + len(cells)
    if len(edges) != expected_edge_count:
        errors.append(f"hyperedge cardinality mismatch: expected {expected_edge_count}, got {len(edges)}")
    if method_ids != set(METHOD_FAMILIES):
        errors.append("method registry does not match METHOD_FAMILIES")

    for edge in edges:
        unknown = set(edge.get("premises", [])) - known_nodes
        if unknown:
            errors.append(f"edge has unknown premises: {edge['edge_id']} -> {sorted(unknown)}")
        if edge.get("conclusion") not in target_ids | cell_ids:
            errors.append(f"edge has unknown conclusion: {edge['edge_id']}")
        if edge.get("oak_level") != 1:
            errors.append(f"edge has unexpected OAK level: {edge['edge_id']}")

    selected = [
        item
        for bucket in ("primary", "secondary", "experiments")
        for item in portfolio.get(bucket, [])
    ]
    computed_coverage = {
        "fronts": len({item["front"] for item in selected}),
        "problems": len({item["problem_id"] for item in selected}),
        "targets": len({item["target_id"] for item in selected}),
        "methods": len({method for item in selected for method in item["methods"]}),
    }
    if computed_coverage != portfolio.get("coverage"):
        errors.append("portfolio coverage mismatch")
    if computed_coverage != report.get("portfolio_coverage"):
        errors.append("report portfolio coverage mismatch")
    if portfolio.get("primary_budget", 0) >= 24:
        primary_fronts = {item["front"] for item in portfolio.get("primary", [])}
        if len(primary_fronts) != 24:
            errors.append("primary portfolio does not cover all 24 fronts")

    source_ids = {row["source_id"] for row in problems}
    registered_source_ids = {row["source_id"] for row in _read_jsonl(output / "sources.jsonl")}
    unresolved = sorted(source_ids - registered_source_ids)
    if unresolved != report.get("unresolved_source_ids"):
        errors.append("unresolved source ledger mismatch")

    return {
        "schema": "omega-problem-atlas-audit-max-strict/3",
        "valid": not errors,
        "errors": errors,
        "counts": {
            "problems": len(problems),
            "targets": len(targets),
            "cells": len(cells),
            "methods": len(methods),
            "hyperedges": len(edges),
        },
        "portfolio_coverage": computed_coverage,
        "report_digest": claimed_report_digest,
        "manifest_digest": report.get("manifest_digest"),
        "solution_claimed": False,
        "proof_claimed": False,
    }
