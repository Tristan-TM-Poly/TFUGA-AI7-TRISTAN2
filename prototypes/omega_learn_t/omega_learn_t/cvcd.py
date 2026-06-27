from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List

_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ0-9_+\-*/=^]+")
_STOP = {
    "the", "and", "for", "with", "dans", "les", "des", "une", "que", "qui",
    "est", "sur", "par", "pour", "plus", "moins", "this", "that", "from", "avec",
    "entre", "comme", "mais", "donc", "vers", "leur", "leurs", "notre", "votre",
}


@dataclass(frozen=True)
class CVCDSignature:
    invariants: List[str]
    residues: List[str]
    compression_ratio: float
    token_entropy: float


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 2 and t.lower() not in _STOP]


def entropy(tokens: Iterable[str]) -> float:
    counts = Counter(tokens)
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def extract_invariants(text: str, limit: int = 12) -> CVCDSignature:
    """Extract a lightweight CVCD signature from notes.

    This is deliberately simple and auditable. It favors repeated terms and formula-like
    tokens as candidate invariants, and flags low-frequency long tokens as residues.
    """

    tokens = tokenize(text)
    counts = Counter(tokens)
    formula_like = [t for t in tokens if any(c in t for c in "=+-*/^_")]
    ranked = sorted(counts.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)

    invariants: List[str] = []
    for token, _ in ranked:
        if token not in invariants:
            invariants.append(token)
        if len(invariants) >= limit:
            break
    for token in formula_like:
        if token not in invariants:
            invariants.append(token)
        if len(invariants) >= limit:
            break

    residues = [token for token, count in counts.items() if count == 1 and len(token) >= 8]
    residues = residues[: max(3, limit // 2)]
    compression_ratio = len(invariants) / max(1, len(tokens))
    return CVCDSignature(
        invariants=invariants,
        residues=residues,
        compression_ratio=compression_ratio,
        token_entropy=entropy(tokens),
    )


def invariant_prompt(invariants: Iterable[str]) -> str:
    items = list(invariants)
    if not items:
        return "Extraire les invariants manquants avant de pratiquer."
    return "Expliquer puis appliquer ces invariants: " + ", ".join(items[:8])
