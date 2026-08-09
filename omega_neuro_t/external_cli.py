from __future__ import annotations

import argparse
import json
from pathlib import Path

from .external import load_verified_jsonl_bundle, run_p1_records_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ω-NEURO P1 on a verified local JSONL bundle")
    parser.add_argument("data", type=Path, help="JSONL observations")
    parser.add_argument("manifest", type=Path, help="DatasetManifest JSON")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--split-seed", default="omega-neuro-p1-external")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records, manifest = load_verified_jsonl_bundle(args.data, args.manifest)
    report = run_p1_records_benchmark(
        records,
        manifest,
        folds=args.folds,
        split_seed=args.split_seed,
    )
    text = json.dumps(report, indent=2 if args.pretty else None, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
