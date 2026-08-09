from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_p1_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω-NEURO P1 reproducible baseline tournament")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--groups", type=int, default=24)
    parser.add_argument("--trials-per-group", type=int, default=8)
    parser.add_argument("--noise-scale", type=float, default=0.03)
    parser.add_argument("--split-seed", default="omega-neuro-p1")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    report = run_p1_benchmark(
        folds=args.folds,
        groups=args.groups,
        trials_per_group=args.trials_per_group,
        noise_scale=args.noise_scale,
        split_seed=args.split_seed,
    )
    text = json.dumps(report, indent=2 if args.pretty else None, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
