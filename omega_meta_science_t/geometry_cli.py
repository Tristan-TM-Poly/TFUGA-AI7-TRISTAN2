"""CLI replay for Ω-DISCOVERY-GEOMETRY-ALGEBRA-T R0.3."""

from __future__ import annotations

import argparse
import json

from .geometry import report_as_dict, run_discovery_geometry_algebra_demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay Discovery Geometry & Algebra R0.3")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    payload = report_as_dict(run_discovery_geometry_algebra_demo())
    print(json.dumps(payload, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
