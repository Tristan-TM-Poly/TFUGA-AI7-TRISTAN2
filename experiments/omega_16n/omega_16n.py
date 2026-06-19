"""Omega 16^n symbolic expansion generator.

This module implements the `x16^n` canon as a safe symbolic generator:

- enumerate small depths exactly;
- summarize large depths without materializing all leaves;
- score paths deterministically;
- keep OAK guardrails in the output.

OAK guardrail:
    Generation is not proof. A path is a candidate, not a certified claim.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable, List, Sequence

HEX = "0123456789ABCDEF"

BRANCHES = {
    "0": "Trace",
    "1": "Transform",
    "2": "Maintain",
    "3": "Hypergraphize",
    "4": "Compress",
    "5": "Expand",
    "6": "Factorize",
    "7": "Invariantize",
    "8": "Residualize",
    "9": "Compose",
    "A": "Generalize",
    "B": "Dualize",
    "C": "Challenge",
    "D": "CertifyLocal",
    "E": "Memorize",
    "F": "Reinject",
}

DEFAULT_M_MINUS_PATTERNS = (
    "FFFF",  # pure reinjection loop without validation
    "AAAA",  # unchecked generalization spiral
    "5555",  # decompression-only expansion
)


@dataclass(frozen=True)
class OmegaPath:
    """One fixed-depth 16-ary expansion path."""

    word: str

    @property
    def depth(self) -> int:
        return len(self.word)

    @property
    def index(self) -> int:
        return hex_word_to_int(self.word)

    @property
    def branches(self) -> List[str]:
        return [BRANCHES[digit] for digit in self.word]


def path_count(depth: int) -> int:
    """Return the raw number of paths in a 16-branch expansion."""

    if depth < 0:
        raise ValueError("depth must be non-negative")
    return 16 ** depth


def int_to_hex_word(value: int, depth: int) -> str:
    """Encode an integer as a fixed-length base-16 path."""

    if depth < 0:
        raise ValueError("depth must be non-negative")
    maximum = path_count(depth)
    if value < 0 or value >= maximum:
        raise ValueError("value outside fixed-depth path range")
    return format(value, f"0{depth}X") if depth else ""


def hex_word_to_int(word: str) -> int:
    """Decode a fixed-length base-16 path."""

    if any(char not in HEX for char in word):
        raise ValueError("path contains non-hex branch")
    return int(word, 16) if word else 0


def enumerate_paths(depth: int, limit: int | None = None) -> List[OmegaPath]:
    """Enumerate paths up to an optional limit.

    This is intended for small depths or sampled frontiers. Use symbolic_summary
    for large depths.
    """

    total = path_count(depth)
    cap = total if limit is None else min(limit, total)
    return [OmegaPath(int_to_hex_word(i, depth)) for i in range(cap)]


def deterministic_score(word: str) -> float:
    """Deterministic CVCD-style score for ranking examples.

    The score intentionally favors balanced paths that include validation-like
    operators (`8`, `C`, `D`, `E`) and penalizes unchecked expansion loops.
    """

    if not word:
        return 1.0

    digits = [int(char, 16) for char in word]
    unique_ratio = len(set(word)) / len(word)
    validation_bonus = sum(1 for char in word if char in "8CDE") / len(word)
    compression_bonus = sum(1 for char in word if char in "467") / len(word)
    loop_penalty = max(word.count(char) for char in set(word)) / len(word)
    risky_bonus = sum(1 for char in word if char in "AF") / len(word)

    raw = unique_ratio + validation_bonus + compression_bonus - 0.5 * loop_penalty - 0.25 * risky_bonus
    # Include a tiny stable tie-breaker from the digit sum.
    raw += (sum(digits) % 17) / 1000.0
    return round(raw, 6)


def similarity(a: str, b: str) -> float:
    """Simple prefix/position similarity in [0, 1]."""

    if not a or not b:
        return 0.0
    length = min(len(a), len(b))
    matches = sum(1 for i in range(length) if a[i] == b[i])
    return matches / max(len(a), len(b))


def oak_adjusted_score(word: str, m_minus_patterns: Sequence[str] = DEFAULT_M_MINUS_PATTERNS) -> float:
    base = deterministic_score(word)
    penalty = max((similarity(word, pattern) for pattern in m_minus_patterns), default=0.0)
    return round(base - 0.75 * penalty, 6)


def top_k_paths(depth: int, k: int = 16, sample_limit: int = 4096) -> List[dict]:
    """Return top-k paths from an exact small enumeration or bounded sample."""

    if k < 0:
        raise ValueError("k must be non-negative")
    if sample_limit <= 0:
        raise ValueError("sample_limit must be positive")

    total = path_count(depth)
    paths = enumerate_paths(depth, limit=min(total, sample_limit))
    ranked = sorted(
        paths,
        key=lambda path: (oak_adjusted_score(path.word), -path.index),
        reverse=True,
    )[:k]
    return [
        {
            "word": path.word,
            "index": path.index,
            "branches": path.branches,
            "score": deterministic_score(path.word),
            "oak_adjusted_score": oak_adjusted_score(path.word),
        }
        for path in ranked
    ]


def symbolic_summary(depth: int, k: int = 16, sample_limit: int = 4096) -> dict:
    """Build an OAK-safe symbolic summary for depth n."""

    total = path_count(depth)
    materialized = min(total, sample_limit)
    return {
        "module": "Omega 16^n Recursive Expansion",
        "status": "EXECUTABLE_SYMBOLIC",
        "depth": depth,
        "raw_path_count": total,
        "materialized_for_frontier": materialized,
        "full_materialization_allowed": depth <= 3,
        "top_k_frontier": top_k_paths(depth, k=k, sample_limit=sample_limit),
        "guardrails": [
            "Generation is not proof.",
            "16^n paths must be compressed, sampled, scored and OAK-gated.",
            "For n > 3, use symbolic summaries or bounded frontiers, not full materialization.",
        ],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Omega 16^n symbolic expansion generator")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=16)
    parser.add_argument("--sample-limit", type=int, default=4096)
    args = parser.parse_args(list(argv) if argv is not None else None)

    print(json.dumps(symbolic_summary(args.depth, args.top_k, args.sample_limit), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
