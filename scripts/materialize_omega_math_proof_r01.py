#!/usr/bin/env python3
"""Materialize the Ω-MATH-PROOF R0.1 discovery pack from text-safe parts.

The GitHub connector is text oriented, so the small source ZIP is stored as
Base85 chunks.  This script reconstructs the bytes, verifies SHA-256 before
extracting, and rejects path traversal.  It intentionally does not download or
commit third-party book PDFs.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / "artifacts" / "omega_math_proof_r01"
MANIFEST = PAYLOAD_DIR / "payload.manifest.json"
DECODED = PAYLOAD_DIR / "decoded"
ARCHIVE = PAYLOAD_DIR / "payload.decoded.zip"


def _safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in zf.infolist():
        target = (destination / member.filename).resolve()
        if target != root and root not in target.parents:
            raise RuntimeError(f"unsafe archive path: {member.filename}")
    zf.extractall(destination)


def main() -> int:
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    part_paths = [PAYLOAD_DIR / name for name in spec["parts"]]
    missing = [str(p) for p in part_paths if not p.exists()]
    if missing:
        raise SystemExit(f"missing payload parts: {missing}")

    encoded = "".join(p.read_text(encoding="ascii").strip() for p in part_paths)
    if len(encoded) != int(spec["encoded_size"]):
        raise SystemExit(
            f"encoded size mismatch: got {len(encoded)}, expected {spec['encoded_size']}"
        )

    raw = base64.b85decode(encoded.encode("ascii"))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != spec["sha256"]:
        raise SystemExit(f"SHA-256 mismatch: got {digest}, expected {spec['sha256']}")
    if len(raw) != int(spec["raw_size"]):
        raise SystemExit(f"raw size mismatch: got {len(raw)}, expected {spec['raw_size']}")

    ARCHIVE.write_bytes(raw)
    if DECODED.exists():
        shutil.rmtree(DECODED)
    DECODED.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as zf:
        _safe_extract(zf, DECODED)

    catalog = DECODED / "catalog" / "books.jsonl"
    count = sum(1 for line in catalog.read_text(encoding="utf-8").splitlines() if line.strip())
    if count != int(spec["expected_catalog_count"]):
        raise SystemExit(
            f"catalog count mismatch after extraction: got {count}, expected {spec['expected_catalog_count']}"
        )

    report = {
        "status": "PASS",
        "sha256": digest,
        "raw_size": len(raw),
        "catalog_count": count,
        "decoded_dir": str(DECODED.relative_to(ROOT)),
    }
    (PAYLOAD_DIR / "materialization_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
