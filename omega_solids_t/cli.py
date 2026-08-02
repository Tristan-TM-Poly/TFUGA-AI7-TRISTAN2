from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .atlas import ARCHETYPE_NAMES, build_archetype, iter_archetypes
from .genome import load_genome, save_genome
from .inverse_design import PropertyObjective, SolidCompiler, maximum_porosity
from .pipeline import SolidPipeline
from .unbounded import (
    AdaptiveSolidFrontier,
    ArchetypeMutationSource,
    FrontierPolicy,
    JSONLGenomeSink,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-solids",
        description="Ω-SOLID-T∞ solid genome, hypergraph, OAK and adaptive frontier engine.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    list_command = commands.add_parser("list-archetypes", help="List the 12 MVP solids.")
    list_command.add_argument("--json", action="store_true")

    emit = commands.add_parser("emit-archetypes", help="Write all archetype genomes to JSON.")
    emit.add_argument("--output-dir", default="generated/omega_solids_t/archetypes")

    analyze = commands.add_parser("analyze", help="Analyze one genome and materialize OAK outputs.")
    analyze_source = analyze.add_mutually_exclusive_group(required=True)
    analyze_source.add_argument("--archetype", choices=ARCHETYPE_NAMES)
    analyze_source.add_argument("--input", help="Path to a solid-genome JSON file.")
    analyze.add_argument("--output-dir", default="generated/omega_solids_t/report")

    atlas = commands.add_parser("atlas", help="Analyze every archetype into separate bundles.")
    atlas.add_argument("--output-dir", default="generated/omega_solids_t/atlas")

    rank = commands.add_parser("rank", help="Rank archetypes for one numerical property target.")
    rank.add_argument("property_name")
    rank.add_argument("target", type=float)
    rank.add_argument("unit")
    rank.add_argument("--tolerance", type=float, required=True)
    rank.add_argument("--maximum-porosity", type=float)
    rank.add_argument("--mode", choices=("target", "maximize", "minimize"), default="target")
    rank.add_argument("--output", default="generated/omega_solids_t/ranking.json")

    frontier = commands.add_parser(
        "frontier",
        help=(
            "Run a finite adaptive candidate campaign. The controller has no permanent total-count "
            "ceiling; --work-items bounds this reproducible experiment."
        ),
    )
    frontier.add_argument("--work-items", type=int, default=10_000)
    frontier.add_argument("--output-dir", default="generated/omega_solids_t/frontier")
    frontier.add_argument("--initial-batch", type=int, default=128)
    frontier.add_argument("--growth-factor", type=float, default=2.0)
    frontier.add_argument("--latency-target-s", type=float, default=1.0)
    frontier.add_argument("--quality-floor", type=float, default=0.70)
    frontier.add_argument("--start", type=int, default=0)
    return parser


def _list_archetypes(as_json: bool) -> int:
    if as_json:
        print(json.dumps(list(ARCHETYPE_NAMES), ensure_ascii=False, indent=2))
    else:
        for name in ARCHETYPE_NAMES:
            print(name)
    return 0


def _emit_archetypes(output_dir: str) -> int:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in ARCHETYPE_NAMES:
        genome = build_archetype(name)
        path = save_genome(genome, output / f"{name}.json")
        manifest.append(
            {
                "name": name,
                "identifier": genome.identifier,
                "path": str(path),
                "fingerprint": genome.fingerprint(),
            }
        )
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"count": len(manifest), "output_dir": str(output)}, indent=2))
    return 0


def _analyze(args: argparse.Namespace) -> int:
    genome = build_archetype(args.archetype) if args.archetype else load_genome(args.input)
    pipeline = SolidPipeline()
    report = pipeline.analyze(genome)
    output = pipeline.materialize(report, args.output_dir)
    print(
        json.dumps(
            {
                "genome_id": genome.identifier,
                "oak_status": report.oak.status.value,
                "oak_score": report.oak.score,
                "output_dir": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report.oak.status.value != "fail" else 2


def _atlas(output_dir: str) -> int:
    output = Path(output_dir)
    pipeline = SolidPipeline()
    manifest = []
    for genome in iter_archetypes():
        report = pipeline.analyze(genome)
        target = pipeline.materialize(report, output / genome.identifier)
        manifest.append(
            {
                "genome_id": genome.identifier,
                "oak_status": report.oak.status.value,
                "oak_score": report.oak.score,
                "path": str(target),
            }
        )
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"count": len(manifest), "output_dir": str(output)}, indent=2))
    return 0


def _rank(args: argparse.Namespace) -> int:
    objective = PropertyObjective(
        args.property_name,
        args.target,
        args.unit,
        args.tolerance,
        mode=args.mode,
    )
    constraints = (
        ()
        if args.maximum_porosity is None
        else (maximum_porosity(args.maximum_porosity),)
    )
    compiler = SolidCompiler((objective,), constraints)
    ranking = compiler.rank(iter_archetypes())
    payload = [candidate.to_dict() for candidate in ranking]
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload[:5], ensure_ascii=False, indent=2))
    return 0


def _frontier(args: argparse.Namespace) -> int:
    if args.work_items < 0:
        raise ValueError("--work-items cannot be negative")
    output = Path(args.output_dir)
    policy = FrontierPolicy(
        initial_batch=args.initial_batch,
        growth_factor=args.growth_factor,
        latency_target_s=args.latency_target_s,
        quality_floor=args.quality_floor,
    )
    controller = AdaptiveSolidFrontier(output, policy=policy)
    source = ArchetypeMutationSource(start=args.start)
    sink = JSONLGenomeSink(output / "accepted-genomes.jsonl")
    report = controller.run(source, sink=sink, work_items=args.work_items)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.status == "completed" else 2


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list-archetypes":
            return _list_archetypes(args.json)
        if args.command == "emit-archetypes":
            return _emit_archetypes(args.output_dir)
        if args.command == "analyze":
            return _analyze(args)
        if args.command == "atlas":
            return _atlas(args.output_dir)
        if args.command == "rank":
            return _rank(args)
        if args.command == "frontier":
            return _frontier(args)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"omega-solids: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
