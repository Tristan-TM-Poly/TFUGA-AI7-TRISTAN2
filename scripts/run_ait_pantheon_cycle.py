"""Runner for AIT-PANTHEON-OMEGA cycles."""

from __future__ import annotations

import argparse
from pathlib import Path

from sage_tristan.ait_pantheon import run_ait_cycle, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AIT-PANTHEON-OMEGA and persist reports/memory.")
    parser.add_argument("--mission", default="Build better AIT systems through OAK, memory negative, FTPCI, HGFM, codex and prototypes.")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--salt", default="cloud")
    args = parser.parse_args()

    result = run_ait_cycle(args.mission, cycles=args.cycles, salt=args.salt)
    write_outputs(result, Path("reports"), Path("memory"), Path("examples"))
    print("AIT-PANTHEON-OMEGA done")
    print("top1", result["top16"][0]["id"], result["top16"][0]["score"])


if __name__ == "__main__":
    main()
