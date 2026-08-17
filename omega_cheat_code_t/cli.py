from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import EvolutionCandidate, EvolutionState, MetaDepthTrial, compile_evolution_plan


def _load_payload(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def compile_payload(payload: dict) -> dict:
    state = EvolutionState(**payload["state"])
    candidates = [EvolutionCandidate(**item) for item in payload["candidates"]]
    meta_trials = [MetaDepthTrial(**item) for item in payload.get("meta_trials", [])]
    plan = compile_evolution_plan(payload["intent"], state, candidates, meta_trials)
    return plan.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a Tristan Cheat Code intent into an OAK-safe evolution plan.")
    parser.add_argument("--input", help="JSON payload path; stdin is used when omitted")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = parser.parse_args()
    result = compile_payload(_load_payload(args.input))
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
