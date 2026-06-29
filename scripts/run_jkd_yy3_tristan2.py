"""Runner for JKD-YY3-Tristan² prototype cycles."""

from __future__ import annotations

import argparse
from pathlib import Path

from sage_tristan.jkd_yy3_tristan2 import run_jyt2, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JKD-YY3-Tristan2 cycle and persist outputs.")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--salt", default="manual")
    args = parser.parse_args()

    result = run_jyt2(cycles=args.cycles, salt=args.salt)
    write_outputs(result, Path("reports"), Path("examples"))
    print("JKD-YY3-Tristan2 done")
    print("top1", result["top1_jkd"]["id"], result["top1_jkd"]["score"])


if __name__ == "__main__":
    main()
