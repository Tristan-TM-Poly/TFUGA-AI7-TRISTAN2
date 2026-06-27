from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .bayes_mastery import mastery_vector
from .core import SkillSpec
from .cvcd import extract_invariants
from .exporters import export_cards_csv, export_json, export_markdown
from .github_bridge import issue_markdown
from .m_minus_registry import MMinusRegistry
from .memory_codec import cards_from_errors, cards_from_invariants, oak_cards, schedule_cards
from .oakbench_learn import oak_questions
from .sage_learning_coach import SageLearningCoach
from .scheduler import build_review_queue
from .storage import JsonlStore


def load_spec(path: str | Path) -> SkillSpec:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return SkillSpec.from_mapping(payload)


def dump(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def build_cards(spec: SkillSpec):
    signature = extract_invariants(" ".join([spec.skill, spec.goal, spec.notes]))
    cards = cards_from_invariants(spec.skill, signature.invariants[:8], spec.tags)
    cards.extend(cards_from_errors(spec.errors, spec.tags))
    cards.extend(oak_cards(spec.skill, oak_questions()[:3], spec.tags))
    return cards


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="omega-learn-t", description="Ω-LEARN-T prototype CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ["inspect", "diagnose", "coach", "cards", "mminus", "oak", "queue", "github-issue"]:
        p = sub.add_parser(name)
        p.add_argument("spec", help="Path to skill JSON")
        if name == "queue":
            p.add_argument("--days", type=int, default=7)
        if name == "github-issue":
            p.add_argument("--type", choices=["learning_goal", "m_minus_error", "oak_test"], default="learning_goal")
            p.add_argument("--output")

    p_init = sub.add_parser("init")
    p_init.add_argument("store", help="Directory for JSONL store")

    p_log = sub.add_parser("log")
    p_log.add_argument("spec", help="Path to skill JSON")
    p_log.add_argument("--store", default=".learning_state")
    p_log.add_argument("--event-type", default="skill_snapshot")

    p_status = sub.add_parser("status")
    p_status.add_argument("--store", default=".learning_state")

    p_export = sub.add_parser("export-anki")
    p_export.add_argument("spec")
    p_export.add_argument("--output", required=True)

    p_export_json = sub.add_parser("export-json")
    p_export_json.add_argument("spec")
    p_export_json.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    coach = SageLearningCoach()

    if args.command == "init":
        store = JsonlStore(args.store)
        store.init()
        dump(store.status())
        return

    if args.command == "status":
        dump(JsonlStore(args.store).status())
        return

    if args.command == "log":
        spec = load_spec(args.spec)
        store = JsonlStore(args.store)
        store.save_skill(spec)
        report = coach.inspect(spec)
        event = store.append_event(args.event_type, spec.skill, report)
        dump({"logged": event.to_dict(), "status": store.status()})
        return

    if args.command == "export-anki":
        spec = load_spec(args.spec)
        cards = build_cards(spec)
        path = export_cards_csv(cards, args.output)
        dump({"exported": str(path), "cards": len(cards)})
        return

    if args.command == "export-json":
        spec = load_spec(args.spec)
        path = export_json(coach.coach(spec), args.output)
        dump({"exported": str(path)})
        return

    spec = load_spec(args.spec)

    if args.command in {"inspect", "diagnose"}:
        dump(coach.inspect(spec))
    elif args.command == "coach":
        print(coach.summarize_markdown(spec))
    elif args.command == "cards":
        dump(schedule_cards(build_cards(spec)))
    elif args.command == "mminus":
        reg = MMinusRegistry(spec.errors)
        dump({"errors": reg.to_dicts(), "top_causes": reg.top_causes(), "future_tests": reg.future_tests()})
    elif args.command == "oak":
        dump({"questions": oak_questions(), "report": coach.inspect(spec)["oakbench"]})
    elif args.command == "queue":
        report = coach.inspect(spec)
        tasks = build_review_queue(spec.skill, mastery_vector(spec.evidence), report["cvcd"]["invariants"], spec.errors, days=args.days, tags=spec.tags)
        dump([task.to_dict() for task in tasks])
    elif args.command == "github-issue":
        md = issue_markdown(spec, args.type)
        if args.output:
            path = export_markdown(md, args.output)
            dump({"exported": str(path)})
        else:
            print(md)


if __name__ == "__main__":
    main()
