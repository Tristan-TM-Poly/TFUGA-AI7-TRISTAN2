"""Unified module dispatcher for Ω-ACTIONS-T∞."""
from __future__ import annotations

import argparse

from . import cli, delta_ci, evidence, telemetry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m omega_actions_t")
    parser.add_argument("command", choices=("static", "delta", "telemetry", "evidence"))
    args, rest = parser.parse_known_args(argv)
    if args.command == "static":
        return cli.main(rest)
    if args.command == "delta":
        return delta_ci.main(rest)
    if args.command == "telemetry":
        return telemetry.main(rest)
    return evidence.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
