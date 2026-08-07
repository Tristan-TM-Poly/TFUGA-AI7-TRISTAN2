from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .identity_graph import audit_identity_graph, compile_identity_graph


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-identities",
        description="Compile and audit conservative mathematical identity and alias graphs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="compile R0.4 imports into an R0.5 identity graph")
    compile_parser.add_argument("--import-jsonl", action="append", required=True)
    compile_parser.add_argument("--decision-json", action="append", default=[])
    compile_parser.add_argument("--output-dir", required=True)

    audit_parser = sub.add_parser("audit", help="strictly audit an R0.5 materialization")
    audit_parser.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_identity_graph(
            tuple(Path(path) for path in args.import_jsonl),
            Path(args.output_dir),
            decision_paths=tuple(Path(path) for path in args.decision_json),
        )
    else:
        result = audit_identity_graph(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
