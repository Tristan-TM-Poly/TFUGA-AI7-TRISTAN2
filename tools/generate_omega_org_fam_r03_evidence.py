#!/usr/bin/env python3
"""Generate the Ω-ORG-FAM-T R0.3 synthetic evidence benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from omega_org_fam_t.evidence_benchmark import audit_benchmark, generate_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--cases", type=int, default=8_388_608)
    parser.add_argument("--shard-cases", type=int, default=524_288)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    manifest = generate_benchmark(args.root, cases=args.cases, shard_cases=args.shard_cases, clean=args.clean)
    output = args.root / "generated" / "omega_org_fam_t_r03_evidence_benchmark"
    audit = audit_benchmark(output)
    (output / "oak-report.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if not audit["valid"]:
        raise SystemExit(json.dumps(audit))
    print(json.dumps({"manifest": manifest, "audit": audit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
