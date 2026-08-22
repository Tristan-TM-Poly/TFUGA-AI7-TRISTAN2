"""CLI for Ω-OMNISTORY-T∞ R6."""
from __future__ import annotations

import argparse
import json

from .engine import continuity_errors, derive_residuals, projection_plan
from .factory import eighth_fire_story
from .meta import GeneratorRegistry, propose_generator_from_residual
from .regeneration import default_book0, regeneration_receipt


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def validate_reference() -> int:
    story = eighth_fire_story()
    errors = continuity_errors(story)
    _print({"story_id": story.story_id, "valid": not errors, "errors": errors})
    return 0 if not errors else 1


def show_projection(backend: str) -> int:
    _print(projection_plan(eighth_fire_story(), backend))
    return 0


def meta_demo() -> int:
    story = eighth_fire_story()
    residuals = derive_residuals(story)
    registry = GeneratorRegistry(tuple(propose_generator_from_residual(item) for item in residuals))
    _print({
        "residuals": [item.residual_id for item in residuals],
        "generated_generators": list(registry.ids()),
        "rule": "Generator != Judge",
    })
    return 0


def regenerate_demo() -> int:
    story = eighth_fire_story()
    receipt = regeneration_receipt(
        story,
        recovered_capabilities=(
            "story-ir", "continuity", "canon-ledger", "residual-field",
            "meta-generation", "crystallization", "regeneration",
        ),
    )
    _print({
        "story_id": receipt.story_id,
        "closure": receipt.closure,
        "book0_digest": receipt.book0_digest,
        "story_digest": receipt.story_digest,
        "book0": default_book0().__dict__,
    })
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-omnistory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-reference")
    projection = sub.add_parser("projection")
    projection.add_argument("backend", choices=("manga", "anime", "novel", "game"))
    sub.add_parser("meta-demo")
    sub.add_parser("regenerate-demo")
    args = parser.parse_args(argv)
    if args.command == "validate-reference":
        return validate_reference()
    if args.command == "projection":
        return show_projection(args.backend)
    if args.command == "meta-demo":
        return meta_demo()
    if args.command == "regenerate-demo":
        return regenerate_demo()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
