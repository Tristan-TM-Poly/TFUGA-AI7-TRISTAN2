from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .audit import audit_streaming_atlas
from .benchmark import benchmark_scaling
from .model import RuntimePolicy
from .streaming import ingest_jsonl, materialize_synthetic_campaign, query_portfolio


def _add_policy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--shard-target-bytes", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--max-disk-bytes", type=int)
    parser.add_argument("--sqlite-busy-timeout-ms", type=int, default=30_000)


def _policy(args: argparse.Namespace) -> RuntimePolicy:
    return RuntimePolicy(
        batch_size=args.batch_size,
        shard_target_bytes=args.shard_target_bytes,
        max_disk_bytes=args.max_disk_bytes,
        sqlite_busy_timeout_ms=args.sqlite_busy_timeout_ms,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-stream",
        description="Stream, index, resume, query and audit large problem-atlas campaigns.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="stream JSONL into a SQLite WAL atlas")
    ingest.add_argument("--input-jsonl", required=True)
    ingest.add_argument("--output-dir", required=True)
    ingest.add_argument("--resume", action="store_true")
    ingest.add_argument("--max-items", type=int)
    ingest.add_argument("--no-clean", action="store_true")
    _add_policy_args(ingest)

    synthetic = sub.add_parser("synthetic", help="materialize a deterministic synthetic campaign")
    synthetic.add_argument("--output-dir", required=True)
    synthetic.add_argument("--cell-count", type=int, required=True)
    synthetic.add_argument("--problem-count", type=int, default=72)
    synthetic.add_argument("--target-count", type=int, default=16)
    synthetic.add_argument("--resume", action="store_true")
    synthetic.add_argument("--max-items", type=int)
    synthetic.add_argument("--no-clean", action="store_true")
    _add_policy_args(synthetic)

    query = sub.add_parser("query", help="query a bounded portfolio without loading the atlas")
    query.add_argument("output_dir")
    query.add_argument("--limit", type=int, default=24)
    query.add_argument("--max-per-front", type=int, default=2)
    query.add_argument("--min-priority", type=int)

    audit = sub.add_parser("audit", help="replay-audit SQLite, shards and Merkle receipts")
    audit.add_argument("output_dir")
    audit.add_argument("--chunk-size", type=int, default=10_000)

    benchmark = sub.add_parser("benchmark", help="run finite scale and memory measurements")
    benchmark.add_argument("--output-dir", required=True)
    benchmark.add_argument("--sizes", type=int, nargs="+", required=True)
    _add_policy_args(benchmark)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "ingest":
        result = ingest_jsonl(
            Path(args.input_jsonl),
            Path(args.output_dir),
            policy=_policy(args),
            resume=args.resume,
            max_items=args.max_items,
            clean=not args.no_clean,
        )
    elif args.command == "synthetic":
        result = materialize_synthetic_campaign(
            Path(args.output_dir),
            cell_count=args.cell_count,
            problem_count=args.problem_count,
            target_count=args.target_count,
            policy=_policy(args),
            resume=args.resume,
            max_items=args.max_items,
            clean=not args.no_clean,
        )
    elif args.command == "query":
        result = query_portfolio(
            Path(args.output_dir),
            limit=args.limit,
            max_per_front=args.max_per_front,
            min_priority=args.min_priority,
        )
    elif args.command == "audit":
        result = audit_streaming_atlas(Path(args.output_dir), chunk_size=args.chunk_size)
    else:
        result = benchmark_scaling(
            Path(args.output_dir),
            sizes=args.sizes,
            policy=_policy(args),
        )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    if args.command == "audit":
        return 0 if result.get("valid") is True else 1
    if args.command in {"ingest", "synthetic"}:
        return 0 if result.get("status") != "failed" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
