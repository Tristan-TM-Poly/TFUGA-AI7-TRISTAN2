from __future__ import annotations

import argparse
import json
from pathlib import Path


def _count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Ω-MATH-PROOF-RESEARCH-OS R0.1 contract checker")
    parser.add_argument("--catalog", type=Path, help="Path to books.jsonl")
    parser.add_argument("--expected", type=int, default=64)
    args = parser.parse_args()

    if args.catalog is None:
        print(json.dumps({"component": "omega-math-proof-research-os", "version": "0.1.0"}))
        return 0

    if not args.catalog.exists():
        raise SystemExit(f"catalog not found: {args.catalog}")

    count = _count_jsonl(args.catalog)
    report = {
        "catalog": str(args.catalog),
        "count": count,
        "expected": args.expected,
        "status": "PASS" if count == args.expected else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if count == args.expected else 2


if __name__ == "__main__":
    raise SystemExit(main())
