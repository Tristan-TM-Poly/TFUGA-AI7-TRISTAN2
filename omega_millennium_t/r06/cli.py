from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .evidence_graph import audit_evidence_graph, compile_evidence_graph


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-evidence",
        description="Compile and audit OAK-safe claim-evidence-barrier graphs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="compile canonical identities and evidence bundles")
    compile_parser.add_argument("--canonical-problems", required=True)
    compile_parser.add_argument("--bundle-json", action="append", required=True)
    compile_parser.add_argument("--output-dir", required=True)

    audit_parser = sub.add_parser("audit", help="strictly audit an R0.6 graph")
    audit_parser.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_evidence_graph(
            Path(args.canonical_problems),
            tuple(Path(path) for path in args.bundle_json),
            Path(args.output_dir),
        )
    else:
        result = audit_evidence_graph(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
