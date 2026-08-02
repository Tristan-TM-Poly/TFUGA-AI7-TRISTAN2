#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, io, json, lzma, tarfile
from pathlib import Path

# R0.3 MAX materialization trigger: the payload is immutable and SHA-256 verified.
COMPRESSED_SHA256 = "01f6401d2bb2bb6cf91b7da218a4492af9bd335cdc31abea345af4faf02b7298"


def materialize(root: Path, payload_dir: Path) -> list[str]:
    encoded = "".join(path.read_text(encoding="ascii") for path in sorted(payload_dir.glob("*.b85")))
    compressed = base64.b85decode(encoded.encode("ascii"))
    if hashlib.sha256(compressed).hexdigest() != COMPRESSED_SHA256:
        raise RuntimeError("Ω-PCT R0.3 payload digest mismatch")
    archive_bytes = lzma.decompress(compressed, format=lzma.FORMAT_XZ)
    written: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if root.resolve() not in target.parents:
                raise RuntimeError(f"unsafe generated path: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())
            written.append(member.name)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--payload-dir", default="tools/omega_pct_r03max_payload")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    written = materialize(root, root / args.payload_dir)
    manifest = root / "generated/omega_pct_t/r03max-generation.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "system": "Ω-PCT∞ R0.3 MAX",
        "generated_files": len(written),
        "paths": written,
        "permanent_total_ceiling": None,
        "automatic_scientific_promotion": False,
    }
    manifest.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
