#!/usr/bin/env python3
"""Materialize Ω-ORG-FAM-T R0.1 Massive without a permanent record ceiling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_org_fam_t.atlas import compile_atlas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--family-records", type=int, default=262_144)
    parser.add_argument("--family-shard-size", type=int, default=16_384)
    parser.add_argument("--evidence-shard-size", type=int, default=32_768)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    manifest = compile_atlas(
        root / "generated" / "omega_org_fam_t_r01",
        family_records=args.family_records,
        family_shard_size=args.family_shard_size,
        evidence_shard_size=args.evidence_shard_size,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
