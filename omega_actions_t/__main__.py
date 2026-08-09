"""Unified module dispatcher for Ω-ACTIONS-T∞."""
from __future__ import annotations

import argparse

from . import cache_tensor, cli, compiler, delta_ci, digital_twin, evidence, sharding, telemetry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m omega_actions_t")
    parser.add_argument(
        "command",
        choices=("static", "delta", "telemetry", "evidence", "shard", "twin", "cache", "compile"),
    )
    args, rest = parser.parse_known_args(argv)
    dispatch = {
        "static": cli.main,
        "delta": delta_ci.main,
        "telemetry": telemetry.main,
        "evidence": evidence.main,
        "shard": sharding.main,
        "twin": digital_twin.main,
        "cache": cache_tensor.main,
        "compile": compiler.main,
    }
    return dispatch[args.command](rest)


if __name__ == "__main__":
    raise SystemExit(main())
