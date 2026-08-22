"""CLI for Ω-COMPUTE-PHYSICS-T∞ R0.1.

Examples
--------
python -m omega_compute_physics_t.cli demo --output artifacts/compute-atlas/demo.json
python -m omega_compute_physics_t.cli fit-jsonl samples.jsonl --target wall_time_s --output atlas.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .atlas import ComplexityAtlas, ResourceSample
from .profiler import machine_fingerprint, profile_call


def _demo_kernel(n: int) -> int:
    # Deliberately simple deterministic workload for a smoke-test atlas.
    total = 0
    for i in range(n):
        total += (i * i + 3 * i + 7) % 97
    return total


def _run_demo(output: Path, repeats: int) -> int:
    atlas = ComplexityAtlas(
        name="omega-compute-physics-r01-demo",
        machine=machine_fingerprint(),
        software={"kernel": "deterministic modular accumulation"},
    )
    for n in (200, 400, 800, 1600, 3200, 6400):
        result = profile_call(
            _demo_kernel,
            n,
            variables={"n": float(n)},
            repeats=repeats,
            warmups=1,
            metadata={"campaign": "r01-demo"},
        )
        atlas.add_sample(result.sample)

    model = atlas.fit(
        "wall_time_s",
        max_total_degree=2,
        include_logs=True,
        include_xlogx=True,
    )
    atlas.write_json(output)
    print(model.equation())
    print(json.dumps(model.certificate(), indent=2, sort_keys=True))
    print(f"atlas: {output}")
    return 0


def _load_jsonl(path: Path) -> list[ResourceSample]:
    samples: list[ResourceSample] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload: dict[str, Any] = json.loads(raw)
            samples.append(
                ResourceSample(
                    variables=payload["variables"],
                    resources=payload["resources"],
                    metadata=payload.get("metadata", {}),
                )
            )
        except Exception as exc:  # noqa: BLE001 - CLI should identify the bad line.
            raise ValueError(f"invalid sample at {path}:{line_number}: {exc}") from exc
    return samples


def _fit_jsonl(
    source: Path,
    target: str,
    output: Path,
    degree: int,
    no_logs: bool,
) -> int:
    atlas = ComplexityAtlas(name=source.stem, machine=machine_fingerprint())
    atlas.extend(_load_jsonl(source))
    model = atlas.fit(
        target,
        max_total_degree=degree,
        include_logs=not no_logs,
        include_xlogx=not no_logs,
    )
    atlas.write_json(output)
    print(model.equation())
    print(json.dumps(model.certificate(), indent=2, sort_keys=True))
    print(f"atlas: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-compute-physics",
        description="OAK-safe empirical multivariate resource atlas prototype",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="profile a deterministic kernel and fit a runtime law")
    demo.add_argument("--output", type=Path, default=Path("artifacts/compute-atlas/demo.json"))
    demo.add_argument("--repeats", type=int, default=5)

    fit = sub.add_parser("fit-jsonl", help="fit a resource surface from ResourceSample JSONL")
    fit.add_argument("source", type=Path)
    fit.add_argument("--target", required=True)
    fit.add_argument("--output", type=Path, default=Path("complexity_atlas.json"))
    fit.add_argument("--degree", type=int, default=2)
    fit.add_argument("--no-logs", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        return _run_demo(args.output, args.repeats)
    if args.command == "fit-jsonl":
        return _fit_jsonl(args.source, args.target, args.output, args.degree, args.no_logs)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
