from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .job_system import audit_job_campaign, compile_job_campaign, replay_job


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-jobs",
        description="Run, resume, replay and audit allowlisted deterministic research jobs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="execute or checkpoint a job campaign")
    compile_parser.add_argument("--bundle-json", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    compile_parser.add_argument("--max-jobs", type=int)
    compile_parser.add_argument("--resume", action="store_true")

    audit_parser = sub.add_parser("audit", help="strictly replay-audit a campaign")
    audit_parser.add_argument("output_dir")

    replay_parser = sub.add_parser("replay", help="replay one materialized job")
    replay_parser.add_argument("--campaign-dir", required=True)
    replay_parser.add_argument("--job-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_job_campaign(
            Path(args.bundle_json),
            Path(args.output_dir),
            max_jobs=args.max_jobs,
            resume=args.resume,
        )
    elif args.command == "audit":
        result = audit_job_campaign(Path(args.output_dir))
    else:
        result = replay_job(Path(args.campaign_dir), args.job_id)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
