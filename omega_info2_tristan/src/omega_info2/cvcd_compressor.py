"""CVCD compressor MVP for Ω-INFO²-T.

CVCD here means conservative extraction of candidate invariants and residue.
It is not a proof engine. It estimates compression gain and preserves what was
lost or not confidently represented.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from math import log2

from .models import InfoObject, ProvenanceStep, clamp01

_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ0-9_²Ω\-]{3,}")

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "dans", "avec",
    "pour", "une", "des", "les", "qui", "que", "est", "sont", "information", "objet",
}


@dataclass(slots=True)
class CVCDInvariant:
    label: str
    weight: float
    support_count: int
    source: str = "token_frequency"


@dataclass(slots=True)
class CVCDReport:
    invariants: list[CVCDInvariant] = field(default_factory=list)
    residue: list[str] = field(default_factory=list)
    original_token_count: int = 0
    compressed_token_count: int = 0
    compression_gain: float = 0.0
    fidelity_warning: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class CVCDCompressor:
    """Extract candidate invariants from text or InfoObject fields."""

    def __init__(self, max_invariants: int = 12) -> None:
        self.max_invariants = max_invariants

    def compress_text(self, text: str) -> CVCDReport:
        tokens = [token.lower() for token in _TOKEN_RE.findall(text)]
        meaningful = [token for token in tokens if token not in _STOPWORDS]
        counts = Counter(meaningful)
        original_count = max(len(tokens), 1)

        invariants: list[CVCDInvariant] = []
        for token, count in counts.most_common(self.max_invariants):
            weight = count * _information_weight(token, original_count)
            invariants.append(CVCDInvariant(label=token, weight=clamp01(weight), support_count=count))

        compressed_count = sum(1 for _ in invariants)
        compression_gain = clamp01(1.0 - (compressed_count / original_count))
        residue = _residue_from_counts(counts, invariants)
        warning = None
        if compression_gain > 0.95 and original_count > 100:
            warning = "Very high compression: verify that rare critical details were not lost."
            residue.append(warning)

        return CVCDReport(
            invariants=invariants,
            residue=residue,
            original_token_count=original_count,
            compressed_token_count=compressed_count,
            compression_gain=compression_gain,
            fidelity_warning=warning,
        )

    def compress_info_object(self, obj: InfoObject) -> CVCDReport:
        text_parts = []
        text_parts.extend(claim.text for claim in obj.claims)
        text_parts.extend(obj.concepts)
        text_parts.extend(obj.equations)
        if obj.raw_object.content_preview:
            text_parts.append(obj.raw_object.content_preview)
        report = self.compress_text("\n".join(text_parts))
        obj.scores.compression_gain = report.compression_gain
        obj.concepts = sorted(set(obj.concepts + [item.label for item in report.invariants]))
        obj.oak.residue.extend(report.residue)
        obj.provenance.transformations.append(
            ProvenanceStep(
                operation="compress_cvcd_mvp",
                tool="CVCDCompressor",
                tool_version="0.1.0",
                confidence=0.55,
                information_loss=1.0 - report.compression_gain,
            )
        )
        return report


def _information_weight(token: str, original_count: int) -> float:
    # Lightweight proxy: frequency support scaled by token specificity.
    specificity = min(1.0, log2(max(len(token), 2)) / 8.0)
    return specificity / max(1.0, log2(original_count + 1.0))


def _residue_from_counts(counts: Counter[str], invariants: list[CVCDInvariant]) -> list[str]:
    invariant_labels = {item.label for item in invariants}
    rare_terms = [term for term, count in counts.items() if count == 1 and term not in invariant_labels]
    residue: list[str] = []
    if rare_terms:
        residue.append("Rare terms preserved as residue: " + ", ".join(sorted(rare_terms)[:20]))
    return residue
