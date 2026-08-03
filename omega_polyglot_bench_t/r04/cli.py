"""CLI for building, autotuning and inspecting Ω-POLYGLOT R0.4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .autotune import autotune, save_report
from .build import BACKENDS, PROFILES, build_native
from .robust import robust_autotune, save_robust_report


def _csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _ints(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="omega-polyglot-r04")
    sub = root.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--backends", default=",".join(BACKENDS))
    build.add_argument("--profiles", default=",".join(PROFILES))
    tune = sub.add_parser("autotune")
    tune.add_argument("--build-native", action="store_true")
    tune.add_argument("--backends", default=",".join(BACKENDS))
    tune.add_argument("--profiles", default=",".join(PROFILES))
    tune.add_argument("--algorithms", default="affine,affine_chain,sum,dot")
    tune.add_argument("--sizes", default="16,256,4096,100000,1000000")
    tune.add_argument("--warmups", type=int, default=3)
    tune.add_argument("--repetitions", type=int, default=15)
    tune.add_argument("--output", type=Path, default=Path("omega-polyglot-r04-report.json"))
    robust = sub.add_parser("robust")
    robust.add_argument("--build-native", action="store_true")
    robust.add_argument("--backends", default=",".join(BACKENDS))
    robust.add_argument("--profiles", default=",".join(PROFILES))
    robust.add_argument("--algorithms", default="affine,affine_chain,sum,dot")
    robust.add_argument("--sizes", default="4096,100000,1000000")
    robust.add_argument("--warmups", type=int, default=3)
    robust.add_argument("--repetitions", type=int, default=15)
    robust.add_argument("--trials", type=int, default=5)
    robust.add_argument("--output", type=Path, default=Path("omega-polyglot-r04-robust.json"))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    backends = _csv(args.backends)
    profiles = _csv(args.profiles)
    if args.command == "build":
        print(json.dumps(build_native(backends=backends, profiles=profiles), indent=2, sort_keys=True))
        return 0
    if args.build_native:
        print(json.dumps(build_native(backends=backends, profiles=profiles), indent=2, sort_keys=True))
    if args.command == "robust":
        payload = robust_autotune(
            trials=args.trials,
            sizes=_ints(args.sizes),
            backends=backends,
            profiles=profiles,
            algorithms=_csv(args.algorithms),
            warmups=args.warmups,
            repetitions=args.repetitions,
        )
        save_robust_report(payload, args.output)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    report = autotune(
        sizes=_ints(args.sizes),
        backends=backends,
        profiles=profiles,
        algorithms=_csv(args.algorithms),
        warmups=args.warmups,
        repetitions=args.repetitions,
    )
    save_report(report, args.output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
