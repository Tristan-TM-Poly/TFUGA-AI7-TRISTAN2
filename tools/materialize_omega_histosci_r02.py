#!/usr/bin/env python3
"""One-shot deterministic materializer for Ω-HISTOSCI-HG-T∞ R0.2.

Reconstructs a reviewed, compressed source payload from repository shards,
writes the R0.2 package/docs/tests/schemas/workflow, materializes 8,192 branch
cells and 65,536 research cells, and executes the focused OAKBench.

The generated corpus is a software research fixture. It does not certify
historical truth, source completeness, global exhaustiveness, or decolonial
completeness.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
PARTS_DIR = ROOT / "tools/omega_histosci_r02_payload"
PAYLOAD_SHA256 = "11367099b3a3cfb4e26be6d713af4ef4faa9ccca29c91b4c95109202754223fa"
EXPECTED_TEMPLATE_FILES = 34


def load_payload() -> dict[str, str]:
    parts = sorted(PARTS_DIR.glob("part_*.txt"))
    if not parts:
        raise RuntimeError("no R0.2 payload parts found")
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in parts)
    digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()
    if digest != PAYLOAD_SHA256:
        raise RuntimeError(f"payload hash mismatch: {digest}")
    raw = zlib.decompress(base64.b85decode(encoded.encode("ascii")))
    mapping = json.loads(raw.decode("utf-8"))
    if len(mapping) != EXPECTED_TEMPLATE_FILES:
        raise RuntimeError(f"expected {EXPECTED_TEMPLATE_FILES} templates, got {len(mapping)}")
    return mapping


def write_templates(mapping: dict[str, str]) -> list[Path]:
    written: list[Path] = []
    for relative, content in sorted(mapping.items()):
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        written.append(target)
    return written


def patch_pyproject() -> Path:
    path = ROOT / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    entry = 'omega-histoscience-r02 = "omega_histosci_hg_t.r02.cli:main"'
    if entry not in text:
        anchor = 'omega-histoscience = "omega_histosci_hg_t.cli:main"'
        if anchor not in text:
            raise RuntimeError("cannot locate omega-histoscience CLI entry")
        text = text.replace(anchor, anchor + "\n" + entry)
        path.write_text(text, encoding="utf-8", newline="\n")
    return path


def run(*args: str) -> None:
    subprocess.check_call([sys.executable, *args], cwd=ROOT)


def materialize_and_verify() -> dict[str, object]:
    output = ROOT / "data/omega_histosci_hg/r02"
    run("-m", "omega_histosci_hg_t.r02.cli", "materialize", "--output-dir", str(output))
    run(
        "-m", "compileall", "-q",
        "omega_histosci_hg_t/r02",
        "tests/test_omega_histosci_r02.py",
        "examples/omega_histosci_r02_demo.py",
    )
    run("-m", "pytest", "-q", "tests/test_omega_histosci_r02.py")
    run(
        "-m", "omega_histosci_hg_t.r02.cli", "oakbench",
        "--output", "/tmp/omega-histoscience-r02-oak.json",
    )
    return json.loads((output / "materialization_manifest.json").read_text(encoding="utf-8"))


def main() -> int:
    mapping = load_payload()
    written = write_templates(mapping)
    patch_pyproject()
    manifest = materialize_and_verify()
    summary = {
        "written_template_files": len(written),
        "branch_cells": manifest["counts"]["branch_cells"],
        "research_cells": manifest["counts"]["research_cells"],
        "expanded_logical_frontier": manifest["logical_frontiers"]["expanded_cells"],
        "permanent_total_cap": None,
        "historical_truth_certified": False,
        "source_completeness_claimed": False,
        "global_exhaustiveness_claimed": False,
        "software_validation_only": True,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
