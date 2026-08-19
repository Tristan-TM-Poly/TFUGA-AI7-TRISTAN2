#!/usr/bin/env python3
"""One-shot deterministic materializer for Ω-HISTOSCI-HG-T∞ R0.2.

Reconstructs the reviewed compressed payload, writes the R0.2 package and
materializes 8,192 branch cells plus 65,536 research cells. Generated cells are
software fixtures; this script never certifies historical truth or completeness.
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
EXPECTED_PARTS = (
    "part_000.txt",
    "part_001.txt",
    "part_002.txt",
    "part_004.txt",
    "part_006.txt",
    "part_008.txt",
    "part_010.txt",
)


def load_encoded_payload() -> tuple[str, bool]:
    """Return canonical Base85 and whether the known legacy overlap was repaired.

    The historical source blob for ``part_008`` accidentally contains the full
    ``part_010`` suffix. The canonical payload hash was generated from the
    non-overlapping sequence. We repair only that exact, auditable condition;
    every other mismatch fails closed.
    """
    chunks: dict[str, str] = {}
    for name in EXPECTED_PARTS:
        path = PARTS_DIR / name
        if not path.is_file():
            raise RuntimeError(f"missing R0.2 payload shard: {name}")
        chunks[name] = path.read_text(encoding="utf-8").strip()

    repaired_overlap = False
    suffix = chunks["part_010.txt"]
    part_008 = chunks["part_008.txt"]
    if part_008.endswith(suffix):
        candidate = part_008[: -len(suffix)]
        if not candidate:
            raise RuntimeError("R0.2 overlap repair would empty part_008")
        chunks["part_008.txt"] = candidate
        repaired_overlap = True

    encoded = "".join(chunks[name] for name in EXPECTED_PARTS)
    digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()
    if digest != PAYLOAD_SHA256:
        raise RuntimeError(f"payload hash mismatch after canonicalization: {digest}")
    return encoded, repaired_overlap


def load_payload() -> tuple[dict[str, str], bool]:
    encoded, repaired_overlap = load_encoded_payload()
    raw = zlib.decompress(base64.b85decode(encoded.encode("ascii")))
    mapping = json.loads(raw.decode("utf-8"))
    if len(mapping) != EXPECTED_TEMPLATE_FILES:
        raise RuntimeError(
            f"expected {EXPECTED_TEMPLATE_FILES} templates, got {len(mapping)}"
        )
    return mapping, repaired_overlap


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
        "-m",
        "compileall",
        "-q",
        "omega_histosci_hg_t/r02",
        "tests/test_omega_histosci_r02.py",
        "examples/omega_histosci_r02_demo.py",
    )
    run("-m", "pytest", "-q", "tests/test_omega_histosci_r02.py")
    run(
        "-m",
        "omega_histosci_hg_t.r02.cli",
        "oakbench",
        "--output",
        "/tmp/omega-histoscience-r02-oak.json",
    )
    return json.loads(
        (output / "materialization_manifest.json").read_text(encoding="utf-8")
    )


def main() -> int:
    mapping, repaired_overlap = load_payload()
    written = write_templates(mapping)
    patch_pyproject()
    manifest = materialize_and_verify()
    summary = {
        "written_template_files": len(written),
        "branch_cells": manifest["counts"]["branch_cells"],
        "research_cells": manifest["counts"]["research_cells"],
        "materialized_cells": (
            manifest["counts"]["branch_cells"]
            + manifest["counts"]["research_cells"]
        ),
        "expanded_logical_frontier": manifest["logical_frontiers"]["expanded_cells"],
        "legacy_overlap_repaired": repaired_overlap,
        "payload_sha256": PAYLOAD_SHA256,
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
