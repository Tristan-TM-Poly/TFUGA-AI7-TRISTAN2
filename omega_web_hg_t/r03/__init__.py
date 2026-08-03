"""Ω-WEB-HG-T∞ R0.3 absorption and provenance search layer."""

from .compiler import audit_absorption, compile_absorption
from .extract import claims_from_sections, detect_duplicates, sentence_candidates, simhash64
from .models import AbsorptionBundle, ClaimCandidate, DuplicateRecord
from .search import SearchIndex

__all__ = [
    "AbsorptionBundle",
    "ClaimCandidate",
    "DuplicateRecord",
    "SearchIndex",
    "audit_absorption",
    "claims_from_sections",
    "compile_absorption",
    "detect_duplicates",
    "sentence_candidates",
    "simhash64",
]
