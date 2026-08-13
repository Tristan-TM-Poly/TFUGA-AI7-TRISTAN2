from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from .github_memory import CapabilityRequest, GitHubMemoryIndex
from .github_memory_evolution import (
    CrossRepositoryCapabilityGraph,
    LLMTFederationCompiler,
    LLMTIdentity,
    ResidualCodeCompiler,
    ReuseOutcomeLearner,
    ReuseOutcomeReceipt,
    TemporalSupersessionMiner,
    compile_evolution_court,
)


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str | None, payload: Mapping[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _outcomes(payload: Mapping[str, Any]) -> tuple[ReuseOutcomeReceipt, ...]:
    rows = payload.get("outcomes", payload.get("receipts", []))
    if not isinstance(rows, list):
        raise TypeError("outcome file must contain a list under outcomes or receipts")
    output = []
    for row in rows:
        item = dict(row)
        item["selected_capabilities"] = tuple(map(str, item.get("selected_capabilities", [])))
        item["evidence_refs"] = tuple(map(str, item.get("evidence_refs", [])))
        output.append(ReuseOutcomeReceipt(**item))
    return tuple(output)


def _identities(payload: Mapping[str, Any]) -> tuple[LLMTIdentity, ...]:
    rows = payload.get("identities", [])
    if not isinstance(rows, list):
        raise TypeError("identity file must contain a list under identities")
    return tuple(LLMTIdentity(**dict(row)) for row in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-github-memory-evolution")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("supersession", "residual", "federation", "court"):
        cmd = sub.add_parser(name)
        cmd.add_argument("index")
        if name != "supersession":
            cmd.add_argument("request")
        if name in {"federation", "court"}:
            cmd.add_argument("--identities")
        if name == "court":
            cmd.add_argument("--outcomes")
        cmd.add_argument("--output")

    learner = sub.add_parser("learn-outcomes")
    learner.add_argument("outcomes")
    learner.add_argument("--output")

    cross = sub.add_parser("cross-repo")
    cross.add_argument("indexes", nargs="+")
    cross.add_argument("--repository", action="append", default=[])
    cross.add_argument("--output")

    args = parser.parse_args(argv)

    if args.command == "learn-outcomes":
        _write(args.output, ReuseOutcomeLearner().learn(_outcomes(_load(args.outcomes))))
        return 0

    if args.command == "cross-repo":
        names = list(args.repository)
        if names and len(names) != len(args.indexes):
            raise ValueError("--repository must be supplied once per index, or omitted")
        indexes = {
            (names[i] if names else f"repo-{i + 1}"): GitHubMemoryIndex.from_dict(_load(path))
            for i, path in enumerate(args.indexes)
        }
        _write(args.output, CrossRepositoryCapabilityGraph().merge(indexes))
        return 0

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    if args.command == "supersession":
        _write(args.output, TemporalSupersessionMiner().mine(index))
        return 0

    request = CapabilityRequest.from_dict(_load(args.request))
    if args.command == "residual":
        _write(args.output, ResidualCodeCompiler(index).compile(request).to_dict())
        return 0

    identities = _identities(_load(args.identities)) if args.identities else ()
    if args.command == "federation":
        _write(args.output, LLMTFederationCompiler(index).compile(request, identities))
        return 0

    outcomes = _outcomes(_load(args.outcomes)) if args.outcomes else ()
    court = compile_evolution_court(index, request, outcome_receipts=outcomes, identities=identities)
    _write(args.output, court)
    return 0 if court["oak"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
