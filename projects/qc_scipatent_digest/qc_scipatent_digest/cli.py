from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import DigestPipeline, PipelineConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qc_scipatent_digest")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["demo", "demo-max", "plus-ultra"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = DigestPipeline(PipelineConfig(mode=args.command)).run(Path(args.out))
    print("QC digest complete")
    print(f"Documents: {result.documents}")
    print(f"Opportunities: {result.opportunities}")
    print(f"Bridges: {result.bridges}")
    print(f"Output: {result.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
