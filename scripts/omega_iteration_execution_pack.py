#!/usr/bin/env python3
"""Build an execution pack from a selected Omega iteration batch."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_CONFIG = {
    "version": "omega.iteration_execution_pack.config.v1",
    "default_repo": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
    "max_items_per_pack": 16,
    "execution_rules": [
        "execute bounded batch only",
        "create tests when possible",
        "verify created files with fetch_file",
        "report quantitative impact after response",
        "do not treat candidate plan as validation",
    ],
}


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def selected_items(selected_batch: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "selected" in selected_batch:
        return list(selected_batch.get("selected", []))
    if "additions" in selected_batch:
        return list(selected_batch.get("additions", []))
    return []


def build_file_plan(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for item in items:
        for path in item.get("files", []) or []:
            rows.append({
                "candidate_id": item.get("id"),
                "path": path,
                "action": item.get("action"),
                "module": item.get("module"),
                "layer": item.get("layer"),
            })
    return rows


def build_test_plan(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for item in items:
        for test in item.get("tests", []) or []:
            rows.append({"candidate_id": item.get("id"), "test": test})
    return rows


def execution_prompt(repo: str, items: List[Dict[str, Any]], rules: List[str]) -> str:
    lines = [
        "# Omega Iteration Execution Pack",
        "",
        f"Repo cible: {repo}",
        "",
        "Execute uniquement ce batch borne. Cree les artifacts utiles, ajoute tests/docs/workflows quand pertinents, puis verifie avec fetch_file.",
        "",
        "## Regles",
    ]
    lines.extend(f"- {rule}" for rule in rules)
    lines.extend(["", "## Candidates"])
    for item in items:
        lines.append(f"- `{item.get('id')}` {item.get('title')} | action={item.get('action')} | files={', '.join(item.get('files', []))}")
    lines.extend([
        "",
        "## Rapport attendu",
        "- fichiers crees/modifies",
        "- tests ajoutes",
        "- statut OAK",
        "- residues M-",
        "- score quantitatif estime apres reponse",
    ])
    return "\n".join(lines) + "\n"


def impact_input(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    artifacts = []
    tests = []
    workflows = []
    residues = []
    for item in items:
        artifacts.extend(item.get("files", []) or [])
        tests.extend(item.get("tests", []) or [])
        residues.extend(item.get("residues", []) or [])
        workflows.extend([path for path in item.get("files", []) or [] if path.startswith(".github/workflows/")])
    return {
        "version": "omega.response_impact_input.v1",
        "summary": "Execution pack generated from selected Omega iteration batch.",
        "artifacts": sorted(set(artifacts)),
        "tests": sorted(set(tests)),
        "workflows": sorted(set(workflows)),
        "residues": sorted(set(residues + ["execution_not_yet_confirmed", "candidate_plan_requires_review"])),
    }


def build_pack(selected_batch: Dict[str, Any], cfg: Dict[str, Any], repo: str = "") -> Dict[str, Any]:
    items = selected_items(selected_batch)[: int(cfg.get("max_items_per_pack", 16))]
    repo = repo or cfg.get("default_repo", "")
    rules = list(cfg.get("execution_rules", []))
    return {
        "version": "omega.iteration_execution_pack.v1",
        "created_unix": time.time(),
        "repo": repo,
        "count": len(items),
        "batch_summary": selected_batch.get("summary", {}),
        "execution_prompt": execution_prompt(repo, items, rules),
        "file_plan": build_file_plan(items),
        "test_plan": build_test_plan(items),
        "oak_gates": sorted({gate for item in items for gate in item.get("oak_gates", [])}),
        "residue_plan": sorted({res for item in items for res in item.get("residues", [])} | {"execution_not_yet_confirmed"}),
        "impact_input": impact_input(items),
        "oak_boundary": {
            "bounded_batch": True,
            "not_all_1024": True,
            "human_review_for_external_action": True,
            "prototype_is_not_proof": True,
        },
    }


def write_outputs(pack: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "execution_pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "execution_prompt.md").write_text(pack["execution_prompt"], encoding="utf-8")
    (out_dir / "impact_input.json").write_text(json.dumps(pack["impact_input"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Omega Iteration Execution Pack", "", f"Repo: {pack['repo']}", f"Candidates: {pack['count']}", "", "## File plan"]
    for row in pack["file_plan"]:
        lines.append(f"- `{row['path']}` from `{row['candidate_id']}`")
    lines.extend(["", "## OAK gates"])
    lines.extend(f"- {gate}" for gate in pack["oak_gates"])
    (out_dir / "EXECUTION_PACK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an execution pack from a selected iteration batch.")
    parser.add_argument("--selected-batch", default="artifacts/iteration_selected_batch/selected_batch.json")
    parser.add_argument("--config", default="configs/omega_iteration_execution_pack.json")
    parser.add_argument("--repo", default="")
    parser.add_argument("--out-dir", default="artifacts/iteration_execution_pack")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    selected = load_json(Path(args.selected_batch), {"selected": []})
    cfg = load_json(Path(args.config), DEFAULT_CONFIG)
    pack = build_pack(selected, cfg, args.repo)
    write_outputs(pack, Path(args.out_dir))
    print(json.dumps({"version": pack["version"], "count": pack["count"], "out_dir": args.out_dir}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
