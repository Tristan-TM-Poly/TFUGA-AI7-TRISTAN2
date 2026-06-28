"""Small deterministic claim extractor for Ω-INFO²-T.

This is not an NLP replacement. It is a safe MVP that extracts candidate
claims and leaves their OAK status as testable/raw rather than true.
"""

from __future__ import annotations

import re

from .models import Claim, OAKStatus

_CLAIM_HINTS = (
    "must",
    "should",
    "is",
    "are",
    "est",
    "sont",
    "doit",
    "devrait",
    "implique",
    "requires",
    "therefore",
    "donc",
    "because",
    "car",
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def extract_candidate_claims(text: str, domain: str = "general", max_claims: int = 25) -> list[Claim]:
    """Extract candidate claims using conservative sentence heuristics."""
    candidates: list[Claim] = []
    for sentence in _SENTENCE_SPLIT.split(text.strip()):
        cleaned = " ".join(sentence.split())
        if len(cleaned) < 20:
            continue
        lowered = cleaned.lower()
        if any(hint in lowered.split() for hint in _CLAIM_HINTS) or "→" in cleaned or "=" in cleaned:
            candidates.append(
                Claim(
                    text=cleaned,
                    domain=domain,
                    uncertainty=0.65,
                    oak_status=OAKStatus.PARSED,
                    next_test="Link claim to source, evidence, counter-evidence, and OAK test.",
                )
            )
        if len(candidates) >= max_claims:
            break
    return candidates
