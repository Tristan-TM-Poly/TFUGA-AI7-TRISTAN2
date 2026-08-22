"""Minimal regenerative kernel for Ω-OMNISTORY R6."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from .models import StoryIR


@dataclass(frozen=True)
class StoryBook0:
    version: str
    story_ir_schema: str
    generator_abi: str
    canon_rules: tuple[str, ...]
    oak_rules: tuple[str, ...]
    rights_rules: tuple[str, ...]
    regeneration_recipes: tuple[str, ...]
    benchmark_ids: tuple[str, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.version.strip(): errors.append("book0.version: required")
        if not self.story_ir_schema.strip(): errors.append("book0.story_ir_schema: required")
        if not self.generator_abi.strip(): errors.append("book0.generator_abi: required")
        if not self.canon_rules: errors.append("book0.canon_rules: required")
        if not self.oak_rules: errors.append("book0.oak_rules: required")
        if not self.rights_rules: errors.append("book0.rights_rules: required")
        if not self.regeneration_recipes: errors.append("book0.regeneration_recipes: required")
        if not self.benchmark_ids: errors.append("book0.benchmark_ids: required")
        return errors


@dataclass(frozen=True)
class RegenerationReceipt:
    story_id: str
    book0_digest: str
    story_digest: str
    expected_capabilities: tuple[str, ...]
    recovered_capabilities: tuple[str, ...]

    @property
    def closure(self) -> float:
        expected = set(self.expected_capabilities)
        if not expected:
            return 1.0
        return len(expected.intersection(self.recovered_capabilities)) / len(expected)


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def default_book0() -> StoryBook0:
    return StoryBook0(
        version="R6",
        story_ir_schema="schemas/omnistory-r6.schema.json",
        generator_abi="plan/generate/verify/repair/compress/regenerate",
        canon_rules=(
            "Generated != Canon",
            "SameCanon != SamePresentation",
            "retcon requires provenance and supersedes",
        ),
        oak_rules=(
            "Generated != Verified",
            "Generator != Judge",
            "MoreMeta != Better",
            "promotion requires frozen benchmark and rollback",
        ),
        rights_rules=(
            "no unauthorized identity imitation",
            "no unauthorized voice cloning",
            "provenance required for promoted assets",
        ),
        regeneration_recipes=(
            "BOOK0 -> GeneratorRegistry -> StoryIR",
            "StoryIR -> backend projection",
            "ResidualField -> candidate generator -> benchmark -> crystal",
        ),
        benchmark_ids=("R6-continuity", "R6-meta-depth", "R6-regeneration"),
    )


def regeneration_receipt(
    story: StoryIR,
    recovered_capabilities: tuple[str, ...],
    expected_capabilities: tuple[str, ...] = (
        "story-ir", "continuity", "canon-ledger", "residual-field",
        "meta-generation", "crystallization", "regeneration",
    ),
    book0: StoryBook0 | None = None,
) -> RegenerationReceipt:
    active_book0 = book0 or default_book0()
    errors = active_book0.validate()
    if errors:
        raise ValueError("; ".join(errors))
    story.require_valid()
    return RegenerationReceipt(
        story_id=story.story_id,
        book0_digest=canonical_digest(asdict(active_book0)),
        story_digest=canonical_digest(story.to_dict()),
        expected_capabilities=expected_capabilities,
        recovered_capabilities=recovered_capabilities,
    )
