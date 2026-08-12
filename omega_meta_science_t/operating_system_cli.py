"""CLI replay for Ω-DISCOVERY-OPERATING-SYSTEM-T∞² R0.4."""

from __future__ import annotations

import argparse
import json

from .operating_system import report_to_dict, run_discovery_os_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay the deterministic R0.4 Discovery OS fixture.")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    payload = report_to_dict(run_discovery_os_demo())
    if args.compact:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(payload, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
