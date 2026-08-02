"""Command-line interface for Ω-RE-T∞ R0.3 research fixtures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .active_learning import MembershipOracle, learn_bounded_mealy
from .causal import Intervention, InterventionResult, intervention_effect
from .cleanroom_agents import AgentIdentity, CleanRoomArtifact, CleanRoomLedger, CleanRoomRole, audit_clean_room
from .genealogy import VersionArtifact, infer_minimum_genealogy, localize_regression
from .grammar import infer_delimited_grammar
from .protocol import ProtocolStep, ProtocolTrace, infer_protocol_model
from .r03_frontier import build_seeds, manifest, materialize
from .sharding import ShardPlan


def _demo_oracle(word: tuple[str, ...]) -> tuple[str, ...]:
    state = 0
    outputs: list[str] = []
    for symbol in word:
        if symbol == "a":
            outputs.append("1" if state else "0")
            state ^= 1
        elif symbol == "b":
            outputs.append("1" if state else "0")
        else:
            raise ValueError(symbol)
    return tuple(outputs)


def command_catalog(_: argparse.Namespace) -> dict[str, object]:
    seeds = build_seeds()
    return {"seed_count": len(seeds), "families": sorted({seed.family for seed in seeds}), "variants": sorted({seed.variant for seed in seeds}), "manifest": manifest()}


def command_learn(_: argparse.Namespace) -> dict[str, object]:
    oracle = MembershipOracle(_demo_oracle)
    report = learn_bounded_mealy(oracle, alphabet=("a", "b"), max_access_depth=4, max_probe_depth=2, validation_depth=4)
    return {
        "states": report.machine.states,
        "transitions": [
            {"source": t.source, "input": t.input_symbol, "output": t.output_symbol, "target": t.target}
            for t in report.machine.transitions
        ],
        "query_count": oracle.query_count,
        "exact_on_domain": report.exact_on_domain,
        "counterexamples": report.counterexamples,
        "digest": report.machine.digest(),
    }


def command_grammar(_: argparse.Namespace) -> dict[str, object]:
    report = infer_delimited_grammar(["1,alpha,true", "2,beta,false", "3,alpha,true"], field_names=("id", "kind", "enabled"))
    return {"delimiter": report.grammar.delimiter, "fields": [{"name": field.name, "kind": field.kind.value, "optional": field.optional} for field in report.grammar.fields], "digest": report.grammar.digest(), "ambiguities": report.ambiguities}


def command_protocol(_: argparse.Namespace) -> dict[str, object]:
    traces = (
        ProtocolTrace((ProtocolStep("HELLO", "READY", 10), ProtocolStep("DATA", "OK", 20), ProtocolStep("CLOSE", "BYE", 5))),
        ProtocolTrace((ProtocolStep("HELLO", "READY", 12), ProtocolStep("CLOSE", "BYE", 6))),
    )
    report = infer_protocol_model(traces)
    return {"states": report.model.states, "transitions": len(report.model.transitions), "conflicts": report.model.conflicts, "digest": report.model.digest()}


def command_causal(_: argparse.Namespace) -> dict[str, object]:
    results = (
        InterventionResult(Intervention("x", 0, intervention_id="c"), "y", (0.0, 0.2, 0.1)),
        InterventionResult(Intervention("x", 1, intervention_id="t"), "y", (1.0, 1.2, 0.9)),
    )
    estimate = intervention_effect(results, treatment_variable="x", outcome_variable="y", treated_value=1, control_value=0)
    return {"treated_mean": estimate.treated_mean, "control_mean": estimate.control_mean, "ate": estimate.average_treatment_effect, "support": estimate.support_score}


def command_cleanroom(_: argparse.Namespace) -> dict[str, object]:
    ledger = CleanRoomLedger()
    for role in CleanRoomRole:
        ledger.register_agent(AgentIdentity(role.value, role, ("synthetic",)))
    observation = CleanRoomArtifact.from_text("obs", "observation", "observer", "behavioral observations")
    ledger.add_artifact(observation)
    specification = CleanRoomArtifact.from_text("spec", "neutral_specification", "specifier", "neutral behavior", source_artifact_ids=("obs",))
    ledger.add_artifact(specification)
    implementation = CleanRoomArtifact.from_text("impl", "implementation", "implementer", "independent code", source_artifact_ids=("spec",))
    ledger.add_artifact(implementation)
    audit_artifact = CleanRoomArtifact.from_text("audit", "audit", "auditor", "review", source_artifact_ids=("obs", "spec", "impl"))
    ledger.add_artifact(audit_artifact)
    audit = audit_clean_room(ledger)
    return {"passed": audit.passed, "blockers": audit.blockers, "warnings": audit.warnings, "role_separation_score": audit.role_separation_score, "provenance_coverage": audit.provenance_coverage, "digest": audit.ledger_digest}


def command_genealogy(_: argparse.Namespace) -> dict[str, object]:
    versions = (
        VersionArtifact("v1", frozenset({"base"}), {"status": "ok"}, "2026-01-01"),
        VersionArtifact("v2", frozenset({"base", "fast"}), {"status": "ok"}, "2026-01-02"),
        VersionArtifact("v3", frozenset({"base", "fast", "new"}), {"status": "bad"}, "2026-01-03"),
    )
    graph = infer_minimum_genealogy(versions)
    lineage = graph.lineage("v3")
    regression = localize_regression(graph, lineage, "status", "ok")
    return {"roots": graph.roots(), "lineage": lineage, "first_bad": regression.first_bad_version, "candidate_edges": regression.candidate_edges, "digest": graph.digest()}


def command_frontier(args: argparse.Namespace) -> dict[str, object]:
    if args.materialize:
        frontier_manifest = materialize(args.materialize)
    else:
        frontier_manifest = manifest()
    plan = ShardPlan.build("omega-re-r03-re1024", frontier_manifest["case_count"], args.shard_size)
    return {"manifest": frontier_manifest, "shard_plan": {"total_items": plan.total_items, "shard_size": plan.shard_size, "shard_count": plan.shard_count, "plan_digest": plan.plan_digest}}


COMMANDS = {
    "catalog": command_catalog,
    "learn-demo": command_learn,
    "grammar-demo": command_grammar,
    "protocol-demo": command_protocol,
    "causal-demo": command_causal,
    "cleanroom-demo": command_cleanroom,
    "genealogy-demo": command_genealogy,
    "frontier": command_frontier,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        child = subparsers.add_parser(name)
        if name == "frontier":
            child.add_argument("--materialize")
            child.add_argument("--shard-size", type=int, default=64)
        child.add_argument("--output")
    args = parser.parse_args(argv)
    payload = COMMANDS[args.command](args)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if getattr(args, "output", None):
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
