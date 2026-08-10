"""Unified module dispatcher for Ω-ACTIONS-T∞."""
from __future__ import annotations

import argparse

from . import (
    auto_optimizer,
    cache_tensor,
    cli,
    compiler,
    delta_ci,
    digital_twin,
    evidence,
    project_surface,
    promotion,
    sharding,
    telemetry,
    trigger_hotspots,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m omega_actions_t")
    parser.add_argument(
        "command",
        choices=(
            "static",
            "delta",
            "telemetry",
            "evidence",
            "shard",
            "twin",
            "cache",
            "compile",
            "candidate",
            "promote",
            "project-surface",
            "hotspots",
        ),
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
        "candidate": auto_optimizer.main,
        "promote": promotion.main,
        "project-surface": project_surface.main,
        "hotspots": trigger_hotspots.main,
    }
    return dispatch[args.command](rest)


if __name__ == "__main__":
    raise SystemExit(main())
