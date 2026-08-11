from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import load_json
from .discovery_bridge import bridge_catalog, write_bridge_specs
from .cvcd import extract_primitives
from .registry import validate_transition


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-skillgen-bridge")
    sub = parser.add_subparsers(dest="cmd", required=True)

    bridge = sub.add_parser("generator-bridge")
    bridge.add_argument("out")
    bridge.add_argument("--domain")
    bridge.add_argument("--family")
    bridge.add_argument("--status")
    bridge.add_argument("--limit", type=int, default=20)
    bridge.add_argument("--root")

    primitive = sub.add_parser("primitives")
    primitive.add_argument("specs", nargs="+")
    primitive.add_argument("--min-support", type=int, default=2)

    promotion = sub.add_parser("promotion-check")
    promotion.add_argument("before")
    promotion.add_argument("after")
    promotion.add_argument("evidence")

    args = parser.parse_args()
    if args.cmd == "generator-bridge":
        specs = bridge_catalog(domain=args.domain, family=args.family, status=args.status, limit=args.limit, root=args.root)
        files = write_bridge_specs(specs, args.out)
        emit({"count": len(specs), "files": files})
        return 0
    if args.cmd == "primitives":
        emit(extract_primitives([load_json(path) for path in args.specs], args.min_support))
        return 0
    if args.cmd == "promotion-check":
        errors = validate_transition(args.before, args.after, load_json(args.evidence))
        emit({"status": "PASS" if not errors else "FAIL", "errors": errors})
        return 0 if not errors else 6
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
