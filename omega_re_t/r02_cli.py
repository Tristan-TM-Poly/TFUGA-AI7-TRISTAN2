"""CLI for Ω-RE-T∞ R0.2 foundation modules."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from json import dumps
from pathlib import Path
from tempfile import TemporaryDirectory

from .authorization import (
    AuthorizationAction,
    AuthorizationGate,
    AuthorizationRequest,
    DataClass,
    synthetic_contract,
)
from .frontier import frontier_manifest, materialize, validate_frontier
from .probabilistic import (
    ProbabilisticObservation,
    demo_probabilistic_pair,
    expected_information_gain,
    posterior,
)
from .re16 import catalog, catalog_digest, validate_catalog
from .storage import Checkpoint, SQLiteEvidenceStore
from .timed import choose_temporal_experiment, demo_timed_pair


def _emit(payload, output: str | None) -> None:
    text = dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def command_catalog(arguments) -> int:
    cases = catalog()
    payload = {
        "count": len(cases),
        "digest": catalog_digest(cases),
        "issues": validate_catalog(cases),
        "cases": [
            {**asdict(case), "digest": case.digest}
            for case in cases
        ],
    }
    _emit(payload, arguments.output)
    return 0 if not payload["issues"] else 2


def command_frontier(arguments) -> int:
    issues = validate_frontier()
    if not issues and arguments.materialize:
        materialize(arguments.materialize)
    payload = {
        "issues": issues,
        "manifest": frontier_manifest(),
        "materialized_path": arguments.materialize,
    }
    _emit(payload, arguments.output)
    return 0 if not issues else 2


def command_demo_prob(arguments) -> int:
    left, right = demo_probabilistic_pair()
    candidates = (left, right)
    priors = {left.machine_id: 0.5, right.machine_id: 0.5}
    experiment = ("A", "B")
    gain = expected_information_gain(
        candidates,
        experiment,
        priors,
    )
    outputs = left.sample(experiment, seed=arguments.seed)
    observations = (
        ProbabilisticObservation(experiment, outputs),
    )
    result = posterior(candidates, observations)
    _emit(
        {
            "experiment": experiment,
            "sampled_outputs": outputs,
            "information_gain_bits": gain,
            "posterior": result,
            "truth": left.machine_id,
        },
        arguments.output,
    )
    return 0


def command_demo_timed(arguments) -> int:
    left, right = demo_timed_pair()
    experiments = (
        ("A",),
        ("B",),
        ("A", "B"),
        ("B", "A"),
    )
    selected = choose_temporal_experiment(
        (left, right),
        experiments,
    )
    observation = left.sample(
        selected or ("A",),
        seed=arguments.seed,
    )
    _emit(
        {
            "selected": selected,
            "observation": asdict(observation),
            "log_likelihoods": {
                left.machine_id: left.log_likelihood(observation),
                right.machine_id: right.log_likelihood(observation),
            },
        },
        arguments.output,
    )
    return 0


def command_db_demo(arguments) -> int:
    contract = synthetic_contract("db-demo")
    gate = AuthorizationGate(contract)
    gate.require(
        AuthorizationRequest(
            AuthorizationAction.STORE,
            DataClass.SYNTHETIC,
        )
    )
    with TemporaryDirectory() as directory:
        path = Path(directory) / "evidence.sqlite"
        with SQLiteEvidenceStore(path) as store:
            store.create_campaign(
                "demo",
                contract.digest,
                metadata={"version": "0.2"},
            )
            store.add_observation(
                "obs-1",
                "demo",
                0,
                {"inputs": ["A"], "outputs": ["0"]},
            )
            first = Checkpoint.create(
                "demo",
                0,
                {"round": 0},
            )
            store.add_checkpoint(first)
            second = Checkpoint.create(
                "demo",
                1,
                {"round": 1},
                first.checkpoint_hash,
            )
            store.add_checkpoint(second)
            latest = store.latest_checkpoint("demo")
            payload = {
                "verification_errors": store.verify_campaign("demo"),
                "observations": store.observations("demo"),
                "latest_checkpoint": (
                    asdict(latest) if latest is not None else None
                ),
            }
    _emit(payload, arguments.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-re-r02")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    catalog_parser = subparsers.add_parser("catalog")
    catalog_parser.add_argument("--output")
    catalog_parser.set_defaults(func=command_catalog)

    frontier_parser = subparsers.add_parser("frontier")
    frontier_parser.add_argument("--output")
    frontier_parser.add_argument("--materialize")
    frontier_parser.set_defaults(func=command_frontier)

    probability_parser = subparsers.add_parser("demo-prob")
    probability_parser.add_argument("--seed", type=int, default=0)
    probability_parser.add_argument("--output")
    probability_parser.set_defaults(func=command_demo_prob)

    timed_parser = subparsers.add_parser("demo-timed")
    timed_parser.add_argument("--seed", type=int, default=0)
    timed_parser.add_argument("--output")
    timed_parser.set_defaults(func=command_demo_timed)

    database_parser = subparsers.add_parser("db-demo")
    database_parser.add_argument("--output")
    database_parser.set_defaults(func=command_db_demo)
    return parser


def main(argv=None) -> int:
    arguments = build_parser().parse_args(argv)
    return arguments.func(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
