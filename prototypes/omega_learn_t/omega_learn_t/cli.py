from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import SkillSpec
from .m_minus_registry import MMinusRegistry
from .memory_codec import cards_from_errors, cards_from_invariants, schedule_cards
from .sage_learning_coach import SageLearningCoach
from .cvcd import extract_invariants
from .oakbench_learn import oak_questions


def load_spec(path: str | Path) -> SkillSpec:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return SkillSpec.from_mapping(payload)


def dump(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="omega-learn-t", description="Ω-LEARN-T prototype CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ["inspect", "diagnose", "coach", "cards", "mminus", "oak"]:
        p = sub.add_parser(name)
        p.add_argument("spec", help="Path to skill JSON")

    args = parser.parse_args(argv)
    spec = load_spec(args.spec)
    coach = SageLearningCoach()

    if args.command in {"inspect", "diagnose"}:
        dump(coach.inspect(spec))
    elif args.command == "coach":
        print(coach.summarize_markdown(spec))
    elif args.command == "cards":
        signature = extract_invariants(" ".join([spec.skill, spec.goal, spec.notes]))
        cards = cards_from_invariants(spec.skill, signature.invariants[:8]) + cards_from_errors(spec.errors)
        dump(schedule_cards(cards))
    elif args.command == "mminus":
        reg = MMinusRegistry(spec.errors)
        dump({"errors": reg.to_dicts(), "top_causes": reg.top_causes(), "future_tests": reg.future_tests()})
    elif args.command == "oak":
        dump({"questions": oak_questions(), "report": coach.inspect(spec)["oakbench"]})


if __name__ == "__main__":
    main()
