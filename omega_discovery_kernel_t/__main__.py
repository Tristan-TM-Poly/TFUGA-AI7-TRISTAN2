"""CLI for Ω-DISCOVERY-KERNEL-T∞.

Usage:
    python -m omega_discovery_kernel_t demo --output-dir generated/discovery-kernel
    python -m omega_discovery_kernel_t audit path/to/events.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .demo import build_raman_closed_loop
from .kernel import DiscoveryLedger


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m omega_discovery_kernel_t",
        description="Compile and audit OAK-safe closed-loop discovery event ledgers.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Generate the deterministic Raman closed-loop example.")
    demo.add_argument("--output-dir", default="generated/omega_discovery_kernel_t/raman-r0-1")

    audit = sub.add_parser("audit", help="Audit an existing events.jsonl ledger.")
    audit.add_argument("events_jsonl")
    audit.add_argument("--output-dir", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "demo":
        ledger = build_raman_closed_loop()
        output = ledger.write(args.output_dir)
        print(json.dumps({"output_dir": str(output), **ledger.audit().to_dict()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "audit":
        ledger = DiscoveryLedger.read_jsonl(args.events_jsonl)
        audit = ledger.audit()
        if args.output_dir:
            ledger.write(args.output_dir)
        print(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2))
        return 0 if not any(item.severity == "P0" for item in audit.findings) else 1
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
