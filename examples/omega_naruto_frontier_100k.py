"""Generate and validate a 100,000-record Ω-NARUTO frontier corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from omega_naruto_hmagfm.frontier import FrontierBudget, write_corpus
from omega_naruto_hmagfm.frontier_validation import validate_frontier


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/omega_naruto/frontier-100k"),
    )
    parser.add_argument("--target", type=int, default=100_000)
    parser.add_argument("--shard-records", type=int, default=10_000)
    args = parser.parse_args()

    manifest = write_corpus(
        args.output_dir,
        budget=FrontierBudget(requested_records=args.target),
        shard_records=args.shard_records,
    )
    validation = validate_frontier(args.output_dir)
    summary = {
        "schema": "omega_naruto_frontier.example.v1",
        "target_records": manifest.target_records,
        "written_records": manifest.written_records,
        "axis_cardinality_per_epoch": manifest.axis_cardinality,
        "completed_epochs": manifest.completed_epochs,
        "shards": len(manifest.shards),
        "corpus_sha256": manifest.corpus_sha256,
        "valid": validation.valid,
        "unique_record_ids": validation.unique_record_ids,
        "findings": [finding.code for finding in validation.findings],
        "non_claim": manifest.non_claim,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if validation.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
