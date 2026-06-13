"""Runner for Omega-MGHFM-TGNT prototype cycles."""

from __future__ import annotations

import argparse
from pathlib import Path

from sage_tristan.omega_mghfm_tgnt import run_cycle, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Omega-MGHFM-TGNT and persist reports/examples.")
    parser.add_argument("inputs", nargs="*", default=["prime tensor gaps", "LOG EXP codex", "OAK memory negative", "JKD YY3 Tristan2"])
    args = parser.parse_args()
    result = run_cycle(args.inputs)
    write_outputs(result, Path("reports"), Path("examples"))
    print("Omega-MGHFM-TGNT done")
    print("statuses", result["cycle"]["oak"]["statuses"])


if __name__ == "__main__":
    main()
