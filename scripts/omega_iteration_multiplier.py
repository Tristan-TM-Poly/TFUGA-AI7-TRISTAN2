#!/usr/bin/env python3
"""
Omega Iteration Multiplier.

Generate up to 1024 OAK-safe candidate additions per iteration, grouped into
small reviewable batches with prompts, manifests, and safety gates.

Boundary:
- Produces candidate plans, not unbounded file writes.
- Keeps each batch reviewable and bounded.
- Does not send messages, contact people, or claim validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "omega.iteration_multiplier.config.v1",
    "target_count": 1024,
    "batch_size": 32,
    "layers": ["interface", "oak", "memory", "hgfm", "github", "data", "publication", "spectro", "math", "agents", "docs", "tests", "workflows", "schemas", "benchmarks", "ops"],
    "modules": ["chatgpt_tristan_v2", "publication_atlas", "publication_package_factory", "open_data_harvester", "ait_universe_folder_engine", "omega_math_universe", "omega_spectro_universe", "bayes_tristan", "hgfm_graph_engine", "oak_verifier"],
    "actions": ["add_config", "add_schema", "add_validator", "add_test", "add_workflow", "add_runbook", "add_dashboard", "add_example", "add_prompt_template", "add_oak_card", "add_memory_entry", "add_hgfm_edge", "add_benchmark_plan", "add_publication_package", "add_data_manifest", "add_safety_check"],
    "oak_gates": ["claim_status_required", "human_review_for_external_action", "no_automatic_outreach", "license_review_for_data", "prototype_is_not_proof", "bounded_generation"],
}


@dataclass
class Addition:
    id: str
    index: int
    batch: int
    layer: str
    module: str
    action: str
    title: str
    intent: str
    files: List[str]
    tests: List[str]
    oak_gates: List[str]
    priority: int
    residues: List[str] = field(default_factory=list)

    def to_jsonable(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def stable_id(*parts: str, length: int = 14) -> str:
    return hashlib.sha256("||".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:length]


def slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-").replace("--", "-") or "item"


def load_config(path: Path) -> Dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG


def file_targets(module: str, layer: str, action: str, index: int) -> List[str]:
    base = slug(module)
    act = slug(action)
    if action == "add_test":
        return [f"tests/test_{base}_{index:04d}.py"]
    if action == "add_workflow":
        return [f".github/workflows/{base}-{index:04d}.yml"]
    if action == "add_schema":
        return [f"schemas/{base}/{act}_{index:04d}.json"]
    if action == "add_runbook":
        return [f"ops/{base}/{act}_{index:04d}.md"]
    if action in {"add_config", "add_prompt_template", "add_data_manifest"}:
        return [f"configs/generated/{base}/{act}_{index:04d}.json"]
    if action in {"add_dashboard", "add_example", "add_publication_package", "add_benchmark_plan"}:
        return [f"artifacts/plans/{base}/{act}_{index:04d}.md"]
    return [f"docs/generated/{layer}/{base}_{act}_{index:04d}.md"]


def infer_tests(action: str, module: str) -> List[str]:
    if action in {"add_schema", "add_config", "add_data_manifest"}:
        return ["json_loads", "required_fields", "oak_boundary_present"]
    if action in {"add_validator", "add_test"}:
        return ["unit_test", "negative_case", "cli_smoke"]
    if action == "add_workflow":
        return ["yaml_present", "safe_trigger", "artifact_path_present"]
    if "publication" in module:
        return ["review_only_boundary", "no_automatic_outreach"]
    if "data" in module:
        return ["license_review", "bounded_download"]
    return ["smoke_test", "oak_boundary_present"]


def make_addition(index: int, batch_size: int, cfg: Dict[str, Any], focus: str = "") -> Addition:
    layers = cfg["layers"]
    modules = cfg["modules"]
    actions = cfg["actions"]
    layer = layers[index % len(layers)]
    module = modules[(index // len(layers)) % len(modules)]
    action = actions[(index // (len(layers) * len(modules))) % len(actions)]
    if focus:
        module = focus
    batch = index // batch_size + 1
    aid = "itmul_" + stable_id(index, batch, layer, module, action)
    title = f"{action} for {module} in {layer} layer"
    intent = f"Create a bounded OAK-safe {action} candidate for {module}, connected to {layer}."
    gates = list(cfg.get("oak_gates", []))
    residues: List[str] = []
    if action in {"add_publication_package", "add_prompt_template"}:
        residues.append("review_only_required")
    if action in {"add_data_manifest", "add_benchmark_plan"}:
        residues.append("license_and_baseline_required")
    priority = 100 - ((index * 37) % 100)
    return Addition(
        id=aid,
        index=index,
        batch=batch,
        layer=layer,
        module=module,
        action=action,
        title=title,
        intent=intent,
        files=file_targets(module, layer, action, index),
        tests=infer_tests(action, module),
        oak_gates=gates,
        priority=priority,
        residues=residues,
    )


def build_additions(cfg: Dict[str, Any], count: int, batch_size: int, focus: str = "") -> List[Addition]:
    if count < 1 or count > 4096:
        raise ValueError("count must be between 1 and 4096")
    if batch_size < 1 or batch_size > 256:
        raise ValueError("batch_size must be between 1 and 256")
    return [make_addition(i, batch_size, cfg, focus) for i in range(count)]


def prompt_for_batch(batch: int, additions: List[Addition]) -> str:
    lines = [
        f"# Omega Iteration Batch {batch}",
        "",
        "Tu es ChatGPT dans l ecosysteme Tristan. Execute ce batch de facon OAK-safe.",
        "Ne promets pas de travail futur. Produis maintenant les artifacts possibles.",
        "Verifier les fichiers crees avec fetch_file quand GitHub est disponible.",
        "",
        "## Additions candidates",
    ]
    for add in additions:
        lines.append(f"- {add.id}: {add.title}; files={', '.join(add.files)}; tests={', '.join(add.tests)}")
    lines.extend([
        "",
        "## OAK boundaries",
        "- Review-only for publications and external actions.",
        "- License/provenance required for data.",
        "- Prototype is not proof.",
        "- Keep batch bounded and report residues.",
    ])
    return "\n".join(lines) + "\n"


def write_outputs(additions: List[Addition], out_dir: Path, batch_size: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": "omega.iteration_multiplier.v1",
        "created_unix": time.time(),
        "addition_count": len(additions),
        "batch_size": batch_size,
        "batch_count": max(add.batch for add in additions) if additions else 0,
        "oak_boundary": {
            "candidate_plan_only": True,
            "bounded_generation": True,
            "human_review_for_external_action": True,
            "prototype_is_not_proof": True,
        },
        "additions": [add.to_jsonable() for add in additions],
    }
    (out_dir / "iteration_multiplier_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    by_batch: Dict[int, List[Addition]] = {}
    for add in additions:
        by_batch.setdefault(add.batch, []).append(add)

    dashboard = ["# Omega Iteration Multiplier Dashboard", "", f"Additions: {len(additions)}", f"Batches: {len(by_batch)}", ""]
    for batch, items in sorted(by_batch.items()):
        dashboard.append(f"## Batch {batch}")
        top = sorted(items, key=lambda x: x.priority, reverse=True)[:8]
        for add in top:
            dashboard.append(f"- `{add.id}` priority `{add.priority}`: {add.title}")
        dashboard.append("")
        batch_dir = out_dir / "batches" / f"batch_{batch:03d}"
        batch_dir.mkdir(parents=True, exist_ok=True)
        (batch_dir / "prompt.md").write_text(prompt_for_batch(batch, items), encoding="utf-8")
        (batch_dir / "additions.json").write_text(json.dumps([x.to_jsonable() for x in items], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "ITERATION_MULTIPLIER_DASHBOARD.md").write_text("\n".join(dashboard) + "\n", encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate up to 1024 OAK-safe addition candidates per iteration.")
    parser.add_argument("--config", default="configs/omega_iteration_multiplier.json")
    parser.add_argument("--target-count", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--focus", default="", help="Override module target for all candidates.")
    parser.add_argument("--out-dir", default="artifacts/iteration_multiplier")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    cfg = load_config(Path(args.config))
    additions = build_additions(cfg, args.target_count, args.batch_size, args.focus)
    write_outputs(additions, Path(args.out_dir), args.batch_size)
    print(json.dumps({
        "version": "omega.iteration_multiplier.v1",
        "additions": len(additions),
        "batch_size": args.batch_size,
        "batches": max(add.batch for add in additions),
        "out_dir": args.out_dir,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
