#!/usr/bin/env python3
"""One-shot deterministic materializer for Ω-HISTOSCI-HG-T∞ R0.3 MAX.

Reconstructs a reviewed compressed source payload, validates its global hash,
writes the R0.3 streaming frontier package, patches the CLI registry and runs
the focused OAKBench. Generated coordinates remain software fixtures and are
never promoted to historical facts by this script.
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
PARTS_DIR = ROOT / "tools/omega_histosci_r03_payload"
PAYLOAD_SHA256 = "2f7c7fc677c7ea643b04ba0853c6715b34e0be88df00c85c85a32eab81ae61f9"
EXPECTED_TEMPLATE_FILES = 24


def load_payload() -> dict[str, str]:
    parts = sorted(PARTS_DIR.glob("part_*.txt"))
    if not parts:
        raise RuntimeError("no R0.3 payload parts found")
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in parts)
    digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()
    if digest != PAYLOAD_SHA256:
        raise RuntimeError(f"payload hash mismatch: {digest}")
    raw = zlib.decompress(base64.b85decode(encoded.encode("ascii")))
    mapping = json.loads(raw.decode("utf-8"))
    if len(mapping) != EXPECTED_TEMPLATE_FILES:
        raise RuntimeError(
            f"expected {EXPECTED_TEMPLATE_FILES} templates, got {len(mapping)}"
        )
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
    entry = 'omega-histoscience-r03 = "omega_histosci_hg_t.r03.cli:main"'
    if entry in text:
        return path
    anchors = (
        'omega-histoscience-r02 = "omega_histosci_hg_t.r02.cli:main"',
        'omega-histoscience = "omega_histosci_hg_t.cli:main"',
    )
    for anchor in anchors:
        if anchor in text:
            text = text.replace(anchor, anchor + "\n" + entry)
            path.write_text(text, encoding="utf-8", newline="\n")
            return path
    raise RuntimeError("cannot locate a Histoscience CLI entry")


def run(*args: str) -> None:
    subprocess.check_call([sys.executable, *args], cwd=ROOT)


def validate() -> dict[str, object]:
    run(
        "-m", "compileall", "-q",
        "omega_histosci_hg_t/r03",
        "tests/test_omega_histosci_r03.py",
        "examples/omega_histosci_r03_demo.py",
    )
    run("-m", "pytest", "-q", "tests/test_omega_histosci_r03.py")
    output = Path("/tmp/omega-histoscience-r03-oak.json")
    run(
        "-m", "omega_histosci_hg_t.r03.cli", "oakbench",
        "--records", "100000", "--output", str(output),
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    expected = "CERTIFIED_SOFTWARE_HISTORIOGRAPHIC_STREAMING_FRONTIER_R0_3"
    if report.get("status") != expected:
        raise RuntimeError(f"unexpected OAK status: {report.get('status')}")
    return report


def main() -> int:
    mapping = load_payload()
    written = write_templates(mapping)
    patch_pyproject()
    report = validate()
    summary = {
        "written_template_files": len(written),
        "canonical_frontier": report["counts"]["canonical_frontier"],
        "extended_frontier": report["counts"]["extended_frontier"],
        "streamed_records": report["counts"]["streamed_records"],
        "permanent_total_cap": None,
        "historical_truth_certified": False,
        "source_completeness_claimed": False,
        "global_exhaustiveness_claimed": False,
        "decolonial_completeness_claimed": False,
        "software_validation_only": True,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
