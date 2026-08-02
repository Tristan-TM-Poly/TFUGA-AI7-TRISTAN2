"""CLI demonstrations for the bounded Ω-RE-T∞ R0.4 research layer."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .active_causal import CausalHypothesis, Intervention, select_intervention, update_posterior
from .authenticated_receipts import ReceiptChain
from .baseline_execution import BaselineCase, execute_baseline
from .probabilistic_r04 import DirichletTransitionEstimator, Outcome
from .symbolic_merge import PrefixTreeTransducer


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def probabilistic_demo() -> dict[str, Any]:
    support = {
        ("idle", "ping"): [Outcome("idle", "pong"), Outcome("busy", "delay")],
        ("busy", "ping"): [Outcome("idle", "pong"), Outcome("busy", "delay")],
    }
    estimator = DirichletTransitionEstimator(support, alpha=1.0)
    for _ in range(8):
        estimator.observe("idle", "ping", Outcome("idle", "pong"))
    for _ in range(2):
        estimator.observe("idle", "ping", Outcome("busy", "delay"))
    distribution = estimator.posterior_distribution("idle", "ping")
    return {
        "schema": "omega-re-r04-probabilistic-demo/1.0",
        "distribution": {
            f"{outcome.next_state}:{outcome.output}": probability
            for outcome, probability in distribution.items()
        },
        "entropy_bits": estimator.posterior_entropy("idle", "ping"),
        "claim": "posterior_over_declared_support_only",
    }


def symbolic_demo() -> dict[str, Any]:
    tree = PrefixTreeTransducer.from_traces(
        [
            (("open", "read"), ("ok", "data")),
            (("open", "close"), ("ok", "done")),
            (("reset", "read"), ("ok", "data")),
        ]
    )
    report = tree.merge_report(signature_depth=2)
    return {"schema": "omega-re-r04-symbolic-demo/1.0", **asdict(report)}


def causal_demo() -> dict[str, Any]:
    hypotheses = [
        CausalHypothesis("direct", {"toggle_a": 0.9, "toggle_b": 0.5}),
        CausalHypothesis("indirect", {"toggle_a": 0.2, "toggle_b": 0.5}),
    ]
    interventions = [
        Intervention("toggle_a", cost=1.0, risk=0.05),
        Intervention("toggle_b", cost=1.0, risk=0.05),
    ]
    selected = select_intervention(hypotheses, interventions)
    posterior = update_posterior(hypotheses, selected.intervention, observed_one=True)
    return {
        "schema": "omega-re-r04-causal-demo/1.0",
        "selected": asdict(selected),
        "posterior_after_positive_observation": posterior,
        "claim": "synthetic_intervention_design_only",
    }


def receipt_demo() -> dict[str, Any]:
    chain = ReceiptChain(b"demo-key-not-for-production")
    chain.append("materialized", {"case_count": 4})
    chain.append("executed", {"case_count": 2})
    valid, errors = chain.verify()
    return {
        "schema": "omega-re-r04-receipt-demo/1.0",
        "valid": valid,
        "errors": errors,
        "entries": chain.export(),
        "claim": "hmac_integrity_not_public_key_signature",
    }


def baseline_demo() -> dict[str, Any]:
    cases = [
        BaselineCase("c0", {"value": 1}, 2),
        BaselineCase("c1", {"value": 3}, 6),
        BaselineCase("c2", {"value": 5}, 10),
    ]
    report = execute_baseline(
        baseline="double-v1",
        cases=cases,
        evaluator=lambda payload: payload["value"] * 2,
        logical_cases=1024,
        materialized_cases=1024,
    )
    return {"schema": "omega-re-r04-baseline-demo/1.0", **asdict(report)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "probabilistic-demo",
            "symbolic-demo",
            "causal-demo",
            "receipt-demo",
            "baseline-demo",
            "all",
        ),
    )
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dispatch = {
        "probabilistic-demo": probabilistic_demo,
        "symbolic-demo": symbolic_demo,
        "causal-demo": causal_demo,
        "receipt-demo": receipt_demo,
        "baseline-demo": baseline_demo,
    }
    payload = (
        {name: function() for name, function in dispatch.items()}
        if args.command == "all"
        else dispatch[args.command]()
    )
    _write(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
