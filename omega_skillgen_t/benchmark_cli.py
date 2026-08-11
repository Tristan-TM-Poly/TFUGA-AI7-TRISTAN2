from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import load_json, validate_spec
from .benchmark_bridge import enrich_spec_with_benchmarks, read_benchmark_jsonl


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-skillgen-benchmark")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enrich = sub.add_parser("enrich")
    enrich.add_argument("spec")
    enrich.add_argument("benchmarks")
    enrich.add_argument("out")

    sub.add_parser("audit-atlas")

    args = parser.parse_args()
    if args.cmd == "enrich":
        result = enrich_spec_with_benchmarks(load_json(args.spec), read_benchmark_jsonl(args.benchmarks))
        errors = validate_spec(result)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        emit({"status": "PASS" if not errors else "FAIL", "errors": errors, "benchmark_contracts": len(result.get("benchmark_contracts", [])), "out": args.out})
        return 0 if not errors else 2
    if args.cmd == "audit-atlas":
        from omega_generator_discovery_t.catalog import audit_catalog
        audit = audit_catalog()
        value = audit.to_dict()
        emit(value)
        return 0 if value.get("valid") else 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
