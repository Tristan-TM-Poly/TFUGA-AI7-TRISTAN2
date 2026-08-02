#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path

COMPRESSED_SHA256 = "abdf7220c0435da05657f8f27bca9279532c7d026ba970f6e8cb089a2bcc9c6f"
EXPECTED_TASKS = 8192


def materialize(root: Path, payload_dir: Path) -> list[str]:
    chunks = sorted(payload_dir.glob("*.b85"))
    if not chunks:
        raise RuntimeError("Ω-PCT campaign payload is missing")
    encoded = "".join(path.read_text(encoding="ascii") for path in chunks)
    compressed = base64.b85decode(encoded.encode("ascii"))
    actual = hashlib.sha256(compressed).hexdigest()
    if actual != COMPRESSED_SHA256:
        raise RuntimeError(f"Ω-PCT campaign payload digest mismatch: {actual}")
    archive_bytes = lzma.decompress(compressed, format=lzma.FORMAT_XZ)
    root_resolved = root.resolve()
    written: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if target != root_resolved and root_resolved not in target.parents:
                raise RuntimeError(f"unsafe generated path: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())
            written.append(member.name)
    return written


def count_tasks(root: Path) -> int:
    return sum(
        1
        for path in sorted((root / "data/omega_pct_r03_campaign").glob("tasks-*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize Ω-PCT∞ R0.3 campaign atlas")
    parser.add_argument("--root", default=".")
    parser.add_argument("--payload-dir", default="tools/omega_pct_r03_campaign_payload")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    written = materialize(root, root / args.payload_dir)
    tasks = count_tasks(root)
    if tasks != EXPECTED_TASKS:
        raise RuntimeError(f"expected {EXPECTED_TASKS} tasks, got {tasks}")
    report = {
        "system": "Ω-PCT∞ R0.3 MAX campaign atlas",
        "generated_files": len(written),
        "task_records": tasks,
        "permanent_total_ceiling": None,
        "automatic_scientific_promotion": False,
        "status": "research-task atlas; not particle discoveries",
        "payload_sha256": COMPRESSED_SHA256,
    }
    output = root / "generated/omega_pct_t/r03-campaign-generation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
