from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .compiler import ResearchABICompiler
from .core import Envelope, InvariantCheck, ObjectRef


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compile_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    compiler = ResearchABICompiler()
    refs: dict[str, ObjectRef] = {}
    for item in payload.get("objects", []):
        envelope = Envelope(
            graph=item["graph"],
            object_type=item["object_type"],
            object_id=item["object_id"],
            payload=item.get("payload", {}),
            provenance=tuple(item.get("provenance", [])),
            uncertainty=float(item.get("uncertainty", 0.0)),
            authority=item.get("authority", "read"),
            oak_state=item.get("oak_state", "UNKNOWN"),
        )
        ref = compiler.add_object(envelope)
        refs[item.get("name", ref.key)] = ref

    for item in payload.get("edges", []):
        compiler.link(
            refs[item["source"]],
            refs[item["target"]],
            item["relation"],
            evidence_refs=tuple(refs[name] for name in item.get("evidence", [])),
            causal_claim=bool(item.get("causal_claim", False)),
            uncertainty=float(item.get("uncertainty", 0.0)),
        )

    for item in payload.get("transformations", []):
        compiler.transform(
            operator=item["operator"],
            inputs=tuple(refs[name] for name in item.get("inputs", [])),
            outputs=tuple(refs[name] for name in item.get("outputs", [])),
            assumptions=tuple(item.get("assumptions", [])),
            invariants=tuple(InvariantCheck(**inv) for inv in item.get("invariants", [])),
            evidence_refs=tuple(refs[name] for name in item.get("evidence", [])),
            residuals=tuple(item.get("residuals", [])),
            uncertainty=float(item.get("uncertainty", 0.0)),
            cost=float(item.get("cost", 0.0)),
            authority=item.get("authority", "read"),
            risk=float(item.get("risk", 0.0)),
            rollback=item.get("rollback", ""),
            provenance=tuple(item.get("provenance", [])),
            oak_state=item.get("oak_state", "UNKNOWN"),
            state_before=item.get("state_before"),
            state_after=item.get("state_after"),
        )
    return compiler.compile(max_per_graph=int(payload.get("max_per_graph", 8)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω Universal Research ABI compiler")
    parser.add_argument("fixture", help="JSON fixture containing objects/edges/transformations")
    parser.add_argument("--output", help="optional output JSON path")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    result = compile_fixture(_load(args.fixture))
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=None if args.compact else 2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
