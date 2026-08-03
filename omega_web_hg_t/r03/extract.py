from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable, Mapping

from omega_web_hg_t.models import stable_id
from .models import ClaimCandidate, DuplicateRecord, claim_id, text_digest

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ0-9\"“«])")
_TOKEN = re.compile(r"[\wÀ-ÖØ-öø-ÿ'-]+", flags=re.UNICODE)
_SPACE = re.compile(r"\s+")
_BOILERPLATE = re.compile(
    r"\b(cookie|cookies|privacy policy|politique de confidentialité|accept all|tout accepter|javascript required)\b",
    flags=re.I,
)


def normalize_text(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


def sentence_candidates(text: str, *, min_words: int = 6, min_chars: int = 40, max_chars: int = 1200) -> tuple[str, ...]:
    normalized = normalize_text(text)
    if not normalized:
        return ()
    pieces = []
    for paragraph in re.split(r"\n+", normalized):
        pieces.extend(_SENTENCE_BOUNDARY.split(paragraph))
    result = []
    for piece in pieces:
        candidate = normalize_text(piece).strip(" -–—•")
        words = _TOKEN.findall(candidate)
        if len(candidate) < min_chars or len(candidate) > max_chars or len(words) < min_words:
            continue
        if _BOILERPLATE.search(candidate):
            continue
        result.append(candidate)
    return tuple(dict.fromkeys(result))


def claims_from_sections(
    sections: Iterable[Mapping[str, object]],
    *,
    page_by_id: Mapping[str, Mapping[str, object]],
) -> list[ClaimCandidate]:
    claims: list[ClaimCandidate] = []
    seen: set[str] = set()
    for section in sections:
        page_id = str(section["page_id"])
        page = page_by_id.get(page_id)
        if page is None:
            continue
        for sentence_index, text in enumerate(sentence_candidates(str(section.get("text") or ""))):
            identifier = claim_id(str(section["section_id"]), text)
            if identifier in seen:
                continue
            seen.add(identifier)
            locator = f"{section.get('locator', '')}:sentence:{sentence_index}"
            claims.append(
                ClaimCandidate(
                    claim_id=identifier,
                    page_id=page_id,
                    section_id=str(section["section_id"]),
                    evidence_id=str(page.get("evidence_id") or ""),
                    url=str(page.get("canonical_url") or page.get("final_url") or ""),
                    locator=locator,
                    text=text,
                    text_sha256=text_digest(text),
                    word_count=len(_TOKEN.findall(text)),
                )
            )
    return claims


def simhash64(text: str) -> int:
    vector = [0] * 64
    tokens = [token.lower() for token in _TOKEN.findall(text)]
    for token in tokens:
        digest = int(text_digest(token)[:16], 16)
        for bit in range(64):
            vector[bit] += 1 if digest & (1 << bit) else -1
    value = 0
    for bit, weight in enumerate(vector):
        if weight >= 0:
            value |= 1 << bit
    return value


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def detect_duplicates(claims: Iterable[ClaimCandidate], *, near_distance: int = 3) -> list[DuplicateRecord]:
    items = list(claims)
    duplicates: list[DuplicateRecord] = []
    exact: dict[str, str] = {}
    fingerprints: dict[str, int] = {}
    buckets: dict[tuple[int, int], list[str]] = defaultdict(list)
    by_id = {item.claim_id: item for item in items}

    for item in items:
        normalized_hash = text_digest(normalize_text(item.text).casefold())
        representative = exact.get(normalized_hash)
        if representative is not None:
            duplicates.append(
                DuplicateRecord(
                    duplicate_id=stable_id("duplicate", "exact", representative, item.claim_id),
                    kind="exact",
                    representative_id=representative,
                    member_id=item.claim_id,
                    distance=0,
                    evidence={"normalized_sha256": normalized_hash},
                )
            )
            continue
        exact[normalized_hash] = item.claim_id
        fingerprint = simhash64(item.text)
        fingerprints[item.claim_id] = fingerprint
        compared: set[str] = set()
        near_match: tuple[str, int] | None = None
        for band in range(4):
            key = (band, (fingerprint >> (band * 16)) & 0xFFFF)
            for candidate_id in buckets[key]:
                if candidate_id in compared:
                    continue
                compared.add(candidate_id)
                distance = hamming_distance(fingerprint, fingerprints[candidate_id])
                if distance <= near_distance:
                    if near_match is None or distance < near_match[1]:
                        near_match = (candidate_id, distance)
            buckets[key].append(item.claim_id)
        if near_match is not None:
            representative_id, distance = near_match
            duplicates.append(
                DuplicateRecord(
                    duplicate_id=stable_id("duplicate", "near", representative_id, item.claim_id),
                    kind="near",
                    representative_id=representative_id,
                    member_id=item.claim_id,
                    distance=distance,
                    evidence={
                        "representative_sha256": by_id[representative_id].text_sha256,
                        "member_sha256": item.text_sha256,
                        "simhash_bits": 64,
                    },
                )
            )
    return duplicates
