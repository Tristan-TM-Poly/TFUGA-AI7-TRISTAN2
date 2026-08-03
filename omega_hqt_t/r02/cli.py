from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .campaign import (all_fixtures, compile_public_evidence_campaign, compile_public_evidence_mission, run_r02_benchmark, write_r02_bundle)
from .foundations import PublicEvidencePolicy, source_by_id
from .ingest import ingest_text


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="omega-hqt-r02",
        description="Ω-HQT R0.2 offline public evidence, temporal mirror and Claim–Evidence Graph compiler",
    )
    sub = command.add_subparsers(dest="command", required=True)
    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--hours", type=int, default=24)
    benchmark.add_argument("--output")
    campaign = sub.add_parser("campaign")
    campaign.add_argument("--output-dir", default="generated/omega_hqt_t/r0.2")
    mission = sub.add_parser("mission")
    mission.add_argument("objective")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("path")
    ingest.add_argument("--format", choices=("json", "jsonl", "csv"), required=True)
    ingest.add_argument("--source-id", required=True)
    ingest.add_argument("--output")
    return command


def emit(payload: object, output: str | None = None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    print(text)

def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_r02_benchmark(args.hours)
        emit(report.to_dict(), args.output)
        return 0 if report.passed else 2
    if args.command == "campaign":
        paths = write_r02_bundle(Path(args.output_dir))
        report = compile_public_evidence_campaign(all_fixtures())
        emit({"status": report.status, "evidence_hash": report.evidence_hash, "paths": paths})
        return 0 if report.status.startswith("CERTIFIED") else 2
    if args.command == "mission":
        mission = compile_public_evidence_mission(args.objective)
        emit(mission.to_dict())
        return 0 if mission.status.startswith("READY") else 2
    source = source_by_id(args.source_id)
    text = Path(args.path).read_text(encoding="utf-8")
    result = ingest_text(text, args.format, source, PublicEvidencePolicy())
    payload = {
        "receipt": result.receipt.to_dict(),
        "observations": [item.to_dict() for item in result.observations],
        "quarantine": [item.to_dict() for item in result.quarantine],
    }
    emit(payload, args.output)
    return 0 if not result.quarantine else 2


if __name__ == "__main__":
    raise SystemExit(main())
