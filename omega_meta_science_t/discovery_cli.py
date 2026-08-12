"""CLI replay for Ω-DISCOVERY-DYNAMICS-T R0.2."""

from __future__ import annotations

import argparse
import json

from .discovery import discovery_report_as_dict, run_discovery_dynamics_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay the deterministic Discovery Dynamics R0.2 fixture")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    payload = discovery_report_as_dict(run_discovery_dynamics_demo())
    if args.compact:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(payload, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
