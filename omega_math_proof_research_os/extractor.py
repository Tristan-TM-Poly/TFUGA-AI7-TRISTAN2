from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .contracts import MathArtifactKind

_PREFIXES: tuple[tuple[re.Pattern[str], MathArtifactKind], ...] = (
    (re.compile(r"^\s*definition\b", re.I), "definition"),
    (re.compile(r"^\s*(theorem|proposition|fact)\b", re.I), "theorem"),
    (re.compile(r"^\s*lemma\b", re.I), "lemma"),
    (re.compile(r"^\s*corollary\b", re.I), "corollary"),
    (re.compile(r"^\s*proof\b", re.I), "proof"),
    (re.compile(r"^\s*(counterexample|disproof)\b", re.I), "counterexample"),
    (re.compile(r"^\s*example\b", re.I), "example"),
    (re.compile(r"^\s*exercises?\b", re.I), "exercise"),
    (re.compile(r"^\s*solution\b", re.I), "solution"),
)


@dataclass(frozen=True, slots=True)
class ClassifiedBlock:
    text: str
    kind: MathArtifactKind | None
    confidence: float
    rule: str


def classify_block(text: str) -> ClassifiedBlock:
    """Deterministic baseline classifier.

    This is deliberately conservative.  It provides a reproducible baseline
    that LLMT/ML extractors must beat; it does not infer theoremhood merely
    because prose sounds mathematical.
    """

    stripped = text.strip()
    for pattern, kind in _PREFIXES:
        if pattern.search(stripped):
            return ClassifiedBlock(stripped, kind, 1.0, f"prefix:{pattern.pattern}")
    return ClassifiedBlock(stripped, None, 0.0, "no-explicit-marker")


def classify_blocks(blocks: Iterable[str]) -> list[ClassifiedBlock]:
    return [classify_block(block) for block in blocks if block.strip()]
