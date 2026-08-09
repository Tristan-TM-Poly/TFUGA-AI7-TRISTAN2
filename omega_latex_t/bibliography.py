from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

from .ast import Text
from .models import DocumentIR, Source


class BibliographyError(ValueError):
    pass


_SAFE_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
_DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


@dataclass(frozen=True)
class CitationEntry:
    key: str
    entry_type: str
    fields: Mapping[str, str]

    def __post_init__(self) -> None:
        if not _SAFE_KEY.fullmatch(self.key):
            raise BibliographyError(f"unsafe citation key {self.key!r}")
        if not re.fullmatch(r"[A-Za-z]+", self.entry_type):
            raise BibliographyError(f"unsupported entry type {self.entry_type!r}")

    def to_mapping(self) -> dict[str, Any]:
        return {"key": self.key, "entry_type": self.entry_type.lower(), "fields": dict(sorted((str(k).lower(), str(v)) for k, v in self.fields.items())), "sha256": self.sha256()}

    def sha256(self) -> str:
        raw = json.dumps({"key": self.key, "entry_type": self.entry_type.lower(), "fields": dict(sorted((str(k).lower(), str(v)) for k, v in self.fields.items()))}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(raw).hexdigest()

    def citation_text(self) -> str:
        fields = {str(k).lower(): str(v).strip() for k, v in self.fields.items()}
        author = fields.get("author", "")
        title = fields.get("title", "")
        venue = fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or ""
        year = fields.get("year", "")
        pieces = [x for x in (author, title, venue, year) if x]
        return ". ".join(pieces) if pieces else self.key

    def to_source(self) -> Source:
        fields = {str(k).lower(): str(v).strip() for k, v in self.fields.items()}
        doi = fields.get("doi", "")
        url = fields.get("url", "")
        locator = f"doi:{doi}" if doi else url
        return Source(id=self.key, citation=self.citation_text(), locator=locator, sha256=self.sha256(), metadata={"bibliography": {"entry_type": self.entry_type.lower(), "fields": dict(sorted(fields.items())), "doi": doi, "url": url, "unverified_external_metadata": True}})


def _strip_outer(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and ((text[0] == "{" and text[-1] == "}") or (text[0] == '"' and text[-1] == '"')):
        return text[1:-1].strip()
    return text


def _split_top_level(text: str, delimiter: str = ",") -> list[str]:
    out: list[str] = []
    current: list[str] = []
    brace_depth = 0
    quote = False
    escape = False
    for ch in text:
        if escape:
            current.append(ch); escape = False; continue
        if ch == "\\":
            current.append(ch); escape = True; continue
        if ch == '"' and brace_depth == 0:
            quote = not quote; current.append(ch); continue
        if not quote:
            if ch == "{": brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth < 0: raise BibliographyError("unbalanced braces in BibTeX entry")
            elif ch == delimiter and brace_depth == 0:
                out.append("".join(current).strip()); current.clear(); continue
        current.append(ch)
    if quote or brace_depth != 0: raise BibliographyError("unterminated quote or brace in BibTeX entry")
    if current or text.endswith(delimiter): out.append("".join(current).strip())
    return out


def _extract_entry(text: str, start: int) -> tuple[str, int]:
    open_char = text[start]
    if open_char not in "{(": raise BibliographyError("BibTeX entry must use { } or ( )")
    close_char = "}" if open_char == "{" else ")"
    depth = 1; quote = False; escape = False; i = start + 1
    while i < len(text):
        ch = text[i]
        if escape: escape = False
        elif ch == "\\": escape = True
        elif ch == '"': quote = not quote
        elif not quote:
            if ch == open_char: depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0: return text[start + 1:i], i + 1
        i += 1
    raise BibliographyError("unterminated BibTeX entry")


def parse_bibtex(text: str) -> tuple[CitationEntry, ...]:
    entries: list[CitationEntry] = []
    cursor = 0
    while True:
        match = re.search(r"@([A-Za-z]+)\s*([\{\(])", text[cursor:])
        if not match: break
        entry_type = match.group(1)
        body, next_cursor = _extract_entry(text, cursor + match.start(2))
        parts = _split_top_level(body)
        if not parts or not parts[0]: raise BibliographyError("missing BibTeX citation key")
        key = parts[0].strip(); fields: dict[str, str] = {}
        for part in parts[1:]:
            if not part: continue
            if "=" not in part: raise BibliographyError(f"malformed BibTeX field {part!r}")
            name, raw_value = part.split("=", 1); name = name.strip().lower()
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name): raise BibliographyError(f"unsafe BibTeX field name {name!r}")
            if "#" in raw_value: raise BibliographyError("BibTeX concatenation/macros are not supported in the bounded parser")
            fields[name] = _strip_outer(raw_value)
        entry = CitationEntry(key=key, entry_type=entry_type, fields=fields)
        if any(existing.key == entry.key for existing in entries): raise BibliographyError(f"duplicate BibTeX citation key {entry.key!r}")
        entries.append(entry); cursor = next_cursor
    return tuple(entries)


def entries_to_sources(entries: Iterable[CitationEntry]) -> tuple[Source, ...]:
    return tuple(entry.to_source() for entry in entries)


def attach_bibliography(doc: DocumentIR, entries: Iterable[CitationEntry], *, replace_existing: bool = False) -> DocumentIR:
    incoming = entries_to_sources(entries)
    existing = {} if replace_existing else {source.id: source for source in doc.sources}
    for source in incoming:
        if source.id in existing and existing[source.id] != source: raise BibliographyError(f"source {source.id!r} already exists with different metadata")
        existing[source.id] = source
    provenance = dict(doc.provenance)
    provenance["bibliography_ingest"] = {"entry_count": len(incoming), "parser": "bounded-bibtex-r0.8", "boundary": "parsed bibliography metadata is provenance, not independent verification of the cited work"}
    return replace(doc, sources=tuple(existing[key] for key in sorted(existing)), provenance=provenance)


def source_key(source_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "-", source_id).strip("-")
    if not safe or not safe[0].isalpha(): safe = "src-" + safe
    return safe or "src"


def validate_bibliography(doc: DocumentIR) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []; seen: set[str] = set()
    for source in doc.sources:
        if source.id in seen: findings.append({"code": "BIB_DUPLICATE_SOURCE", "severity": "error", "message": f"duplicate source id {source.id!r}"})
        seen.add(source.id)
        bib = source.metadata.get("bibliography", {}) if isinstance(source.metadata, Mapping) else {}
        if isinstance(bib, Mapping):
            doi = str(bib.get("doi", "")).strip()
            if doi and not _DOI.fullmatch(doi): findings.append({"code": "BIB_DOI_FORMAT", "severity": "warning", "message": f"source {source.id!r} has noncanonical DOI {doi!r}"})
    return findings


def bibliography_report(doc: DocumentIR) -> dict[str, Any]:
    referenced = sorted({source_id for node in doc.nodes for source_id in node.sources})
    by_id = {source.id: source for source in doc.sources}
    sources = [{"id": s.id, "citation": s.citation, "locator": s.locator, "sha256": s.sha256, "metadata": dict(s.metadata), "referenced": s.id in referenced} for s in (by_id[k] for k in sorted(by_id))]
    return {"semantic_hash": doc.semantic_hash(), "sources": sources, "referenced_source_ids": referenced, "findings": validate_bibliography(doc), "boundary": "citation metadata and locators route evidence; they do not establish entailment, truth, priority or replication"}


def bibliography_latex(doc: DocumentIR) -> str:
    referenced = {source_id for node in doc.nodes for source_id in node.sources}
    sources = [source for source in doc.sources if source.id in referenced]
    if not sources: return ""
    lines = [r"\begin{thebibliography}{99}"]
    for source in sorted(sources, key=lambda item: item.id):
        text = source.citation or source.id
        if source.locator: text += f" [{source.locator}]"
        lines.append(rf"\bibitem{{{source_key(source.id)}}} {Text(text).render()}")
    lines.append(r"\end{thebibliography}")
    return "\n".join(lines)
