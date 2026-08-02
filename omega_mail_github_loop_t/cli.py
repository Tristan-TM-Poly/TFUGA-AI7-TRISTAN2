"""CLI for Ω-MAIL-GITHUB-LOOP-T."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .atlas import audit, generate
from .convergence import evaluate_convergence
from .engine import dry_run_email
from .models import IterationMetrics, LoopCase, LoopPolicy, MailCommand


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-mail-github")
    sub = parser.add_subparsers(dest="command", required=True)
    dry = sub.add_parser("dry-run-email", help="Parse and plan one mail command without GitHub mutation")
    dry.add_argument("email", type=Path)
    dry.add_argument("--out", type=Path)
    conv = sub.add_parser("score-iteration")
    conv.add_argument("metrics", type=Path)
    conv.add_argument("--no-gain-count", type=int, default=0)
    conv.add_argument("--failure-count", type=int, default=0)
    gen = sub.add_parser("generate-atlas"); gen.add_argument("root", type=Path)
    aud = sub.add_parser("audit-atlas"); aud.add_argument("root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "dry-run-email":
        result = dry_run_email(args.email.read_text(encoding="utf-8"))
        text = json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0 if result.anti_loop.allowed else 2
    if args.command == "score-iteration":
        metrics = IterationMetrics(**json.loads(args.metrics.read_text(encoding="utf-8")))
        case = LoopCase(
            "MGC-SCORE", MailCommand("owner/repo", "improve", "module", "objective"),
            unchanged_reply_count=args.no_gain_count, repeated_failure_count=args.failure_count,
        )
        result = evaluate_convergence(case, metrics, LoopPolicy())
        print(json.dumps({"decision": result.decision.value, "score": result.score, "reasons": list(result.reasons)}, indent=2))
        return 0
    if args.command == "generate-atlas":
        print(json.dumps(generate(args.root), indent=2, sort_keys=True)); return 0
    if args.command == "audit-atlas":
        result = audit(args.root); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["passed"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
