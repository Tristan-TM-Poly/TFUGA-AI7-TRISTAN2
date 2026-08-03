"""Ontology extraction and conservative semantic normalization."""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable

OMEGA_PATTERN = re.compile(
    r"(?:Ω[\-‑][A-Z0-9][A-Z0-9+²³∞/]*(?:[\-‑][A-Z0-9+²³∞/]+)*[\-‑]T(?:∞)?|OMEGA_[A-Z0-9][A-Z0-9_]*_T)"
)
CORE_NAMES = (
    "OAKGate", "OAKBench", "OAK", "CVCD", "HGFM", "HGFMnD", "AUTO²",
    "Bayes-Tristan", "Noether-Tristan", "Rosette-Tristan", "DCT-Ω", "M⁺", "M⁻",
    "TFUGA", "AI-7", "AIT", "EAIT", "PR Genome", "CreationDNA",
)

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "proof": ("proof", "preuve", "evidence", "claim", "oak", "audit", "falsif", "ledger"),
    "automation": ("auto", "workflow", "agent", "reactor", "pipeline", "orchestra"),
    "software": ("code", "python", "api", "cli", "schema", "github", "test", "package"),
    "mathematics": ("tensor", "graph", "algebra", "transform", "svd", "theorem", "math", "operator"),
    "physics": ("energy", "laser", "opt", "quantum", "gravity", "circuit", "fluid", "plasma"),
    "biology": ("bio", "cell", "protein", "neuro", "organism", "evolution"),
    "materials": ("material", "crystal", "mems", "manufactur", "print", "solid"),
    "knowledge": ("document", "rosette", "knowledge", "information", "atlas", "search", "pdf"),
    "business": ("company", "revenue", "venture", "product", "market", "licens", "startup", "offer"),
    "governance": ("legal", "privacy", "govern", "policy", "quebec", "canada", "permission"),
    "art": ("game", "manga", "story", "world", "narrative", "creative"),
}

COMPLEMENTARY_DOMAINS = {
    frozenset(pair)
    for pair in (
        ("proof", "software"), ("proof", "physics"), ("proof", "biology"),
        ("automation", "knowledge"), ("automation", "business"),
        ("mathematics", "physics"), ("mathematics", "software"),
        ("materials", "physics"), ("knowledge", "business"),
        ("governance", "business"), ("art", "software"),
    )
}

TYPE_ALIASES: dict[str, str] = {
    "document": "document", "pdf": "document", "paper": "document", "article": "document",
    "claim": "claim_graph", "claims": "claim_graph", "assertion": "claim_graph",
    "graph": "knowledge_graph", "hypergraph": "knowledge_graph", "hgfm": "knowledge_graph",
    "code": "source_code", "repository": "source_code", "repo": "source_code",
    "test": "test_suite", "tests": "test_suite", "benchmark": "benchmark",
    "proof": "evidence", "evidence": "evidence", "report": "report",
    "product": "product", "offer": "product", "need": "need", "problem": "need",
    "data": "dataset", "dataset": "dataset", "signal": "dataset",
    "model": "model", "theory": "theory", "simulation": "simulation",
    "pr": "pull_request", "pull request": "pull_request",
}

ARROW_RE = re.compile(
    r"(?P<left>[A-Za-zÀ-ÿ0-9_+²³∞/ .\-]{2,80})\s*(?:→|->|=>)\s*(?P<right>[A-Za-zÀ-ÿ0-9_+²³∞/ .\-]{2,80})"
)
NEED_MARKERS = ("todo", "missing", "manquant", "besoin", "need", "requires", "nécessite", "must add", "next gate")
RISK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "safety": ("weapon", "medical", "diagnos", "high voltage", "laser class", "biohazard", "radiation"),
    "legal": ("patent", "brevet", "copyright", "license", "licence", "regulated"),
    "privacy": ("personal data", "données personnelles", "email", "inbox", "identity"),
    "financial": ("payment", "bank", "revenue", "transaction", "investment"),
    "epistemic": ("universal", "absolute", "infinite", "omniversal", "proof of everything", "certified"),
}


def normalize_system_id(value: str) -> str:
    return value.replace("‑", "-").replace("_", "-").strip()


def tokenize(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9²³∞]+", text)
        if len(token) > 2
    }


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    a, b = set(left), set(right)
    return len(a & b) / len(a | b) if a | b else 0.0


def infer_domains(text: str) -> set[str]:
    lower = text.lower()
    found = {domain for domain, keywords in DOMAIN_KEYWORDS.items() if any(keyword in lower for keyword in keywords)}
    return found or {"general"}


def extract_system_ids(text: str) -> set[str]:
    found = {normalize_system_id(match.group(0)) for match in OMEGA_PATTERN.finditer(text)}
    for name in CORE_NAMES:
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text, re.IGNORECASE):
            found.add(name)
    return found


def canonical_type(fragment: str) -> str:
    words = tokenize(fragment)
    for alias, canonical in TYPE_ALIASES.items():
        if alias in fragment.lower() or alias in words:
            return canonical
    if not words:
        return "artifact"
    return "_".join(sorted(words)[:3])


@dataclass(frozen=True, slots=True)
class Transformation:
    source: str
    target: str
    raw: str
    line_number: int
    need: bool = False


def extract_transformations(text: str) -> list[Transformation]:
    result: list[Transformation] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in ARROW_RE.finditer(line):
            left = match.group("left").strip(" :-")
            right = match.group("right").strip(" :-")
            lower = line.lower()
            is_need = any(marker in lower for marker in NEED_MARKERS)
            result.append(
                Transformation(
                    source=canonical_type(left),
                    target=canonical_type(right),
                    raw=f"{left} -> {right}",
                    line_number=line_number,
                    need=is_need,
                )
            )
    return result


def infer_needs(text: str) -> list[tuple[str, str, int]]:
    needs: list[tuple[str, str, int]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lower = line.lower().strip()
        if any(marker in lower for marker in NEED_MARKERS):
            cleaned = re.sub(r"^[\-*#\s]+", "", line).strip()
            if 4 <= len(cleaned) <= 240:
                needs.append(("artifact", canonical_type(cleaned), line_number))
    return needs


def evidence_strength(path: str, mentions: int, text: str = "") -> float:
    lower = path.lower()
    score = 0.06
    if any(segment in lower.split("/") for segment in ("src", "tools", "core", "prototypes")):
        score += 0.22
    if "test" in lower:
        score += 0.28
    if "schema" in lower:
        score += 0.12
    if "report" in lower or "oak" in lower or "evidence" in lower:
        score += 0.12
    if "docs/canon" in lower:
        score += 0.10
    if re.search(r"\b(pass|passed|benchmark|replicat|measured|mesuré)\b", text, re.IGNORECASE):
        score += 0.08
    return max(0.0, min(1.0, score + 0.045 * math.log1p(max(0, mentions))))


def infer_risks(text: str) -> dict[str, float]:
    lower = text.lower()
    result: dict[str, float] = {}
    for category, keywords in RISK_KEYWORDS.items():
        hits = sum(keyword in lower for keyword in keywords)
        result[category] = min(1.0, hits * (0.18 if category != "epistemic" else 0.11))
    return result


def domain_complementarity(left: Iterable[str], right: Iterable[str]) -> float:
    pairs = {
        frozenset((a, b))
        for a in set(left)
        for b in set(right)
        if a != b
    }
    hits = len(pairs & COMPLEMENTARY_DOMAINS)
    return min(1.0, 0.34 * hits)


def type_compatibility(outputs: Iterable[str], inputs: Iterable[str]) -> float:
    a, b = set(outputs), set(inputs)
    if not a or not b:
        return 0.15
    exact = len(a & b) / max(1, len(b))
    semantic = max((jaccard(tokenize(x.replace("_", " ")), tokenize(y.replace("_", " "))) for x in a for y in b), default=0.0)
    return max(0.0, min(1.0, 0.75 * exact + 0.25 * semantic))
