from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .campaign import MutationCampaignEngine, mutation_specs_from_mapping, mutation_tests_from_mapping
from .counterexamples import CounterexampleForge
from .differential import DifferentialOracle
from .ecology import MutationEcologyEngine
from .io import read_json, write_json
from .metamorphic import MetamorphicEngine, contracts_from_mapping
from .mminus import MMinusCompiler
from .oak import run_oakbench


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-ci-proof-r05", description="Ω-CI R0.5 counterexample forge and mutation ecology")
    sub = parser.add_subparsers(dest="command", required=True)

    mutate = sub.add_parser("mutate")
    mutate.add_argument("--mutants", required=True)
    mutate.add_argument("--tests", required=True)
    mutate.add_argument("--output", required=True)

    forge = sub.add_parser("forge")
    forge.add_argument("--mutants", required=True)
    forge.add_argument("--campaign", required=True)
    forge.add_argument("--seeds", required=True)
    forge.add_argument("--output", required=True)

    meta = sub.add_parser("metamorphic")
    meta.add_argument("--contracts", required=True)
    meta.add_argument("--behaviors", nargs="+", required=True)
    meta.add_argument("--output", required=True)

    diff = sub.add_parser("differential")
    diff.add_argument("--reference", required=True)
    diff.add_argument("--candidates", nargs="+", required=True)
    diff.add_argument("--corpus", required=True)
    diff.add_argument("--claim-id", required=True)
    diff.add_argument("--output", required=True)

    mm = sub.add_parser("compile-mminus")
    mm.add_argument("--counterexamples", required=True)
    mm.add_argument("--output", required=True)
    mm.add_argument("--tests-output")

    eco = sub.add_parser("ecology")
    eco.add_argument("--mutants", required=True)
    eco.add_argument("--tests", required=True)
    eco.add_argument("--seeds", required=True)
    eco.add_argument("--contracts", required=True)
    eco.add_argument("--output-dir", required=True)

    sub.add_parser("oak")
    return parser


def _counterexamples_from_report(raw):
    from .models import Counterexample

    return tuple(
        Counterexample(
            claim_id=str(item["claim_id"]),
            mutant_id=str(item["mutant_id"]),
            property_id=str(item["property_id"]),
            original_input=str(item["original_input"]),
            minimized_input=str(item["minimized_input"]),
            expected_output=str(item["expected_output"]),
            observed_output=str(item["observed_output"]),
            reduction_steps=tuple(str(value) for value in item.get("reduction_steps", [])),
            provenance=tuple(str(value) for value in item.get("provenance", [])),
        )
        for item in raw.get("counterexamples", [])
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "mutate":
        mutants = read_json(args.mutants)
        report = MutationCampaignEngine().run(
            mutation_specs_from_mapping(mutants),
            mutation_tests_from_mapping(read_json(args.tests)),
            target=str(mutants.get("target", "path_normalizer")),
            baseline_behavior=str(mutants.get("baseline_behavior", "exact_prefix")),
        )
        write_json(args.output, report.to_dict())
        print(report.campaign_id)
        return 0
    if args.command == "forge":
        mutants = read_json(args.mutants)
        campaign = read_json(args.campaign)
        report = CounterexampleForge().search(
            mutation_specs_from_mapping(mutants),
            campaign.get("surviving_mutant_ids", []),
            read_json(args.seeds),
            baseline_behavior=str(mutants.get("baseline_behavior", "exact_prefix")),
            claim_id=str(mutants.get("claim_id", "CLAIM-PATH-NORMALIZATION-EXACT-PREFIX")),
            property_id="PROP-EXACT-ONE-PREFIX",
        )
        write_json(args.output, report.to_dict())
        print(report.report_id)
        return 0
    if args.command == "metamorphic":
        report = MetamorphicEngine().evaluate(contracts_from_mapping(read_json(args.contracts)), args.behaviors)
        write_json(args.output, report.to_dict())
        print(report.report_id)
        return 0
    if args.command == "differential":
        corpus_raw = read_json(args.corpus)
        corpus = tuple(str(value) for value in corpus_raw.get("corpus", corpus_raw.get("explicit", [])))
        report = DifferentialOracle().compare(reference_behavior=args.reference, candidate_behaviors=args.candidates, corpus=corpus, claim_id=args.claim_id)
        write_json(args.output, report.to_dict())
        print(report.report_id)
        return 0
    if args.command == "compile-mminus":
        compilation = MMinusCompiler().compile(_counterexamples_from_report(read_json(args.counterexamples)))
        write_json(args.output, compilation.to_dict())
        if args.tests_output:
            Path(args.tests_output).write_text("\n\n".join(compilation.generated_tests) + "\n", encoding="utf-8")
        print(compilation.compilation_id)
        return 0
    if args.command == "ecology":
        report, artifacts = MutationEcologyEngine().run(
            mutants=read_json(args.mutants), tests=read_json(args.tests), seeds=read_json(args.seeds), contracts=read_json(args.contracts)
        )
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, value in artifacts.items():
            write_json(output_dir / f"r05-{name}.json", value)
        tests_path = output_dir / "r05-generated-regressions.py"
        tests_path.write_text("\n\n".join(artifacts["mminus"]["generated_tests"]) + "\n", encoding="utf-8")
        print(report.ecology_id)
        return 0
    if args.command == "oak":
        payload = run_oakbench()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["passed"] else 1
    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
