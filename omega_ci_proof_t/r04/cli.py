from __future__ import annotations

import argparse
import json
import sys

from .bisect import BisectPlanner
from .causal import CausalDiagnosticEngine
from .counterfactual import CounterfactualProjector
from .dossier import CausalDossierBuilder
from .experiments import DiscriminatingExperimentPlanner, experiments_from_mapping
from .io import read_json, write_json
from .minimize import DeltaMinimizer
from .oak import run_oakbench


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-ci-proof-r04",
        description="Ω-CI R0.4 causal diagnosis, minimization and discriminating experiment planning",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    diagnose = sub.add_parser("diagnose")
    diagnose.add_argument("--model", required=True)
    diagnose.add_argument("--observations", required=True)
    diagnose.add_argument("--output", required=True)

    experiments = sub.add_parser("experiments")
    experiments.add_argument("--model", required=True)
    experiments.add_argument("--observations", required=True)
    experiments.add_argument("--experiments", required=True)
    experiments.add_argument("--budget", required=True, type=float)
    experiments.add_argument("--output", required=True)

    minimize = sub.add_parser("minimize")
    minimize.add_argument("--case", required=True)
    minimize.add_argument("--output", required=True)
    minimize.add_argument("--max-evaluations", type=int, default=256)

    bisect = sub.add_parser("bisect")
    bisect.add_argument("--history", required=True)
    bisect.add_argument("--output", required=True)

    dossier = sub.add_parser("dossier")
    dossier.add_argument("--model", required=True)
    dossier.add_argument("--observations", required=True)
    dossier.add_argument("--experiments", required=True)
    dossier.add_argument("--case", required=True)
    dossier.add_argument("--history", required=True)
    dossier.add_argument("--budget", required=True, type=float)
    dossier.add_argument("--output", required=True)

    sub.add_parser("oak")
    return parser


def _diagnose(model_raw, observation_raw):
    engine = CausalDiagnosticEngine.from_mapping(model_raw)
    observations = engine.observations_from_mapping(observation_raw)
    failure_id = str(model_raw["failure_id"])
    return engine, engine.diagnose(failure_id, observations)


def _minimize(case_raw, max_evaluations=256):
    return DeltaMinimizer().minimize_required_tokens_fixture(
        str(case_raw["failure_id"]),
        tuple(str(value) for value in case_raw["items"]),
        tuple(str(value) for value in case_raw["required_tokens"]),
        max_evaluations=max_evaluations,
    )


def _bisect(history_raw):
    return BisectPlanner().plan(
        str(history_raw["failure_id"]),
        tuple(str(value) for value in history_raw["ordered_commits"]),
        str(history_raw["known_good_sha"]),
        str(history_raw["known_bad_sha"]),
        tested_verdicts={str(key): str(value) for key, value in history_raw.get("tested_verdicts", {}).items()},
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "diagnose":
        _, diagnosis = _diagnose(read_json(args.model), read_json(args.observations))
        write_json(args.output, diagnosis.to_dict())
        print(diagnosis.diagnosis_id)
        return 0
    if args.command == "experiments":
        _, diagnosis = _diagnose(read_json(args.model), read_json(args.observations))
        designs = experiments_from_mapping(read_json(args.experiments))
        plan = DiscriminatingExperimentPlanner().plan(diagnosis, designs, budget=args.budget)
        write_json(args.output, plan.to_dict())
        print(plan.plan_id)
        return 0
    if args.command == "minimize":
        receipt = _minimize(read_json(args.case), max_evaluations=args.max_evaluations)
        write_json(args.output, receipt.to_dict())
        print(receipt.reproduction_id)
        return 0 if receipt.preserved_failure else 2
    if args.command == "bisect":
        plan = _bisect(read_json(args.history))
        write_json(args.output, plan.to_dict())
        print(plan.plan_id)
        return 0
    if args.command == "dossier":
        model_raw = read_json(args.model)
        engine, diagnosis = _diagnose(model_raw, read_json(args.observations))
        designs = experiments_from_mapping(read_json(args.experiments))
        discrimination = DiscriminatingExperimentPlanner().plan(diagnosis, designs, budget=args.budget)
        reproduction = _minimize(read_json(args.case))
        bisect_plan = _bisect(read_json(args.history))
        selected_design = None
        if discrimination.recommendations:
            selected_id = discrimination.recommendations[0].experiment_id
            selected_design = next(item for item in designs if item.experiment_id == selected_id)
        worlds = CounterfactualProjector().project(engine.hypotheses, selected_design) if selected_design else ()
        dossier = CausalDossierBuilder().build(diagnosis, discrimination, reproduction, bisect_plan, worlds)
        write_json(args.output, dossier.to_dict())
        print(dossier.dossier_id)
        return 0
    if args.command == "oak":
        payload = run_oakbench()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["passed"] else 1
    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
