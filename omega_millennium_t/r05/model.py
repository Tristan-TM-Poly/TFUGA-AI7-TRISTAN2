from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence

REPORT_SCHEMA = "omega-problem-identity-report/5"
MANIFEST_SCHEMA = "omega-problem-identity-manifest/5"
DECISION_SCHEMA = "omega-problem-identity-decisions/5"
DECISION_ACTIONS = {"merge", "split", "alias"}

DOMAIN_PATTERNS: Mapping[str, tuple[str, ...]] = {
    "integers": ("integer", "integers", "entier", "entiers", "mathbb z", "ℤ"),
    "natural_numbers": ("natural number", "natural numbers", "mathbb n", "ℕ"),
    "real_numbers": ("real number", "real numbers", "mathbb r", "ℝ"),
    "complex_numbers": ("complex number", "complex numbers", "mathbb c", "ℂ"),
    "prime_numbers": ("prime", "primes", "nombre premier", "nombres premiers"),
    "graphs": ("graph", "graphs", "graphe", "graphes"),
    "hypergraphs": ("hypergraph", "hypergraphs", "hypergraphe", "hypergraphes"),
    "groups": ("group", "groups", "groupe", "groupes"),
    "rings": ("ring", "rings", "anneau", "anneaux"),
    "fields": ("field", "fields", "corps"),
    "manifolds": ("manifold", "manifolds", "variété", "variétés"),
    "matrices": ("matrix", "matrices", "matrice"),
    "vectors": ("vector", "vectors", "vecteur", "vecteurs"),
    "partial_differential_equations": (
        "partial differential equation", "partial differential equations", "pde",
        "équation aux dérivées partielles",
    ),
    "probability_spaces": ("probability space", "probability spaces", "espace probabilisé"),
    "metric_spaces": ("metric space", "metric spaces", "espace métrique"),
    "topological_spaces": ("topological space", "topological spaces", "espace topologique"),
}

QUANTIFIER_PATTERNS: Mapping[str, tuple[str, ...]] = {
    "forall": ("∀", "for all", "for every", "every", "pour tout", "toute", "tout"),
    "exists": ("∃", "there exists", "exists", "il existe"),
    "unique_exists": ("∃!", "there exists a unique", "il existe un unique"),
    "implies": ("⇒", "implies", "implique", "alors"),
    "iff": ("⇔", "if and only if", "iff", "si et seulement si"),
    "negation": ("¬", "not", "no", "aucun", "n'existe pas", "ne peut pas"),
}

TITLE_STOPWORDS = {
    "the", "a", "an", "of", "for", "on", "in", "and", "or", "problem",
    "conjecture", "hypothesis", "theorem", "le", "la", "les", "de", "des",
    "du", "pour", "sur", "et", "ou", "problème", "hypothèse", "théorème",
}


@dataclass(frozen=True)
class IdentityRecord:
    record_id: str
    source_id: str
    source_problem_id: str
    title: str
    title_key: str
    alias_keys: tuple[str, ...]
    front: str
    statement: str | None
    statement_fingerprint: str | None
    quantifier_signature: tuple[str, ...]
    domain_signature: tuple[str, ...]
    source_locator: str
    source_verified_at: str | None
    status_receipt_id: str | None
    adapter_provenance_digest: str
    record_digest: str


@dataclass(frozen=True)
class IdentityDecision:
    decision_id: str
    action: str
    record_ids: tuple[str, ...]
    reason: str
    decided_by: str
    decided_at: str
    evidence_refs: tuple[str, ...]
    canonical_record_id: str | None
    decision_digest: str


@dataclass(frozen=True)
class CollisionRecord:
    collision_id: str
    collision_type: str
    record_ids: tuple[str, ...]
    title_key: str | None
    reason_codes: tuple[str, ...]
    review_required: bool
    collision_digest: str


class UnionFind:
    def __init__(self, values: Iterable[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        root_left, root_right = self.find(left), self.find(right)
        if root_left == root_right:
            return
        if root_left < root_right:
            self.parent[root_right] = root_left
        else:
            self.parent[root_left] = root_right


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[\s\-_:/\\|]+", " ", text)
    text = re.sub(r"[^\w\s∀∃¬⇒⇔ℤℕℝℂ]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_statement(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    for old, new in {
        "⟺": "⇔", "<=>": "⇔", " iff ": " ⇔ ", "⟹": "⇒", "=>": "⇒",
        "≤": "<=", "≥": ">=", "−": "-", "–": "-", "—": "-",
    }.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def statement_fingerprint(statement: str | None) -> str | None:
    if statement is None or not statement.strip():
        return None
    return sha256(normalize_statement(statement).encode("utf-8")).hexdigest()


def structural_signature(statement: str | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if statement is None:
        return (), ()
    normalized = normalize_text(statement)

    def present(pattern: str) -> bool:
        token = normalize_text(pattern)
        return bool(token and re.search(rf"\b{re.escape(token)}\b", normalized))

    quantifiers = tuple(
        key for key, patterns in QUANTIFIER_PATTERNS.items()
        if any(pattern in normalized if pattern in "∀∃¬⇒⇔" else present(pattern) for pattern in patterns)
    )
    domains = tuple(
        key for key, patterns in DOMAIN_PATTERNS.items()
        if any(pattern in normalized if pattern in "ℤℕℝℂ" else present(pattern) for pattern in patterns)
    )
    return quantifiers, domains


def parse_iso8601(value: str, field_name: str) -> str:
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} requires timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: row must be an object")
        rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def file_receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.name,
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "rows": sum(1 for line in data.splitlines() if line.strip()),
    }


def build_identity_record(row: Mapping[str, Any]) -> IdentityRecord:
    source_id = str(row.get("source_id", "")).strip()
    source_problem_id = str(row.get("problem_id", "")).strip()
    title = str(row.get("title", "")).strip()
    front = str(row.get("front", "")).strip()
    source_locator = str(row.get("source_locator", "")).strip()
    provenance = str(row.get("adapter_provenance_digest", "")).strip()
    if not all((source_id, source_problem_id, title, front, source_locator, provenance)):
        raise ValueError("identity input is missing required source metadata")
    if row.get("solution_claimed") is not False:
        raise ValueError(f"{source_problem_id}: solution_claimed must be false")
    statement_raw = row.get("statement")
    statement = str(statement_raw).strip() if statement_raw is not None else None
    aliases_raw = row.get("aliases", []) or []
    if not isinstance(aliases_raw, list) or not all(isinstance(item, str) for item in aliases_raw):
        raise ValueError(f"{source_problem_id}: aliases must be a string list")
    aliases = tuple(sorted({normalize_text(item) for item in aliases_raw if normalize_text(item)}))
    quantifiers, domains = structural_signature(statement)
    record_id = f"record::{source_id}::{source_problem_id}::{provenance[:16]}"
    payload = {
        "record_id": record_id,
        "source_id": source_id,
        "source_problem_id": source_problem_id,
        "title": title,
        "title_key": normalize_text(title),
        "alias_keys": aliases,
        "front": front,
        "statement": statement,
        "statement_fingerprint": statement_fingerprint(statement),
        "quantifier_signature": quantifiers,
        "domain_signature": domains,
        "source_locator": source_locator,
        "source_verified_at": row.get("source_verified_at"),
        "status_receipt_id": row.get("status_receipt_id"),
        "adapter_provenance_digest": provenance,
    }
    return IdentityRecord(**payload, record_digest=stable_digest(payload))


def load_identity_decisions(paths: Sequence[str | Path]) -> tuple[IdentityDecision, ...]:
    decisions: list[IdentityDecision] = []
    for path_like in paths:
        path = Path(path_like)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != DECISION_SCHEMA:
            raise ValueError(f"{path}: unsupported decision schema")
        rows = payload.get("decisions")
        if not isinstance(rows, list):
            raise ValueError(f"{path}: decisions must be a list")
        for raw in rows:
            if not isinstance(raw, Mapping):
                raise ValueError(f"{path}: every decision must be an object")
            action = str(raw.get("action", "")).strip()
            ids_raw = raw.get("record_ids")
            if action not in DECISION_ACTIONS:
                raise ValueError(f"{path}: unsupported action {action!r}")
            if not isinstance(ids_raw, list) or len(ids_raw) < 2:
                raise ValueError(f"{path}: decision requires at least two record_ids")
            record_ids = tuple(sorted({str(item).strip() for item in ids_raw if str(item).strip()}))
            if len(record_ids) < 2:
                raise ValueError(f"{path}: decision requires two distinct record_ids")
            reason = str(raw.get("reason", "")).strip()
            decided_by = str(raw.get("decided_by", "")).strip()
            decided_at = parse_iso8601(str(raw.get("decided_at", "")), "decided_at")
            evidence_raw = raw.get("evidence_refs", [])
            if not reason or not decided_by:
                raise ValueError(f"{path}: decision reason and decided_by are required")
            if not isinstance(evidence_raw, list) or not all(isinstance(item, str) for item in evidence_raw):
                raise ValueError(f"{path}: evidence_refs must be a string list")
            canonical_raw = raw.get("canonical_record_id")
            canonical = str(canonical_raw).strip() if canonical_raw is not None else None
            if action == "merge" and canonical is not None and canonical not in record_ids:
                raise ValueError(f"{path}: canonical_record_id must be in record_ids")
            base = {
                "decision_id": str(raw.get("decision_id", "")).strip(),
                "action": action,
                "record_ids": record_ids,
                "reason": reason,
                "decided_by": decided_by,
                "decided_at": decided_at,
                "evidence_refs": tuple(sorted(set(evidence_raw))),
                "canonical_record_id": canonical,
            }
            if not base["decision_id"]:
                raise ValueError(f"{path}: blank decision_id")
            decisions.append(IdentityDecision(**base, decision_digest=stable_digest(base)))
    decisions.sort(key=lambda item: item.decision_id)
    if len({item.decision_id for item in decisions}) != len(decisions):
        raise ValueError("duplicate decision_id")
    return tuple(decisions)


def all_pairs(values: Sequence[str]) -> set[tuple[str, str]]:
    return {
        tuple(sorted((left, right)))
        for index, left in enumerate(values)
        for right in values[index + 1:]
    }


def component_members(uf: UnionFind, record_ids: Iterable[str], root: str) -> set[str]:
    return {record_id for record_id in record_ids if uf.find(record_id) == root}


def union_respects_splits(
    uf: UnionFind,
    left: str,
    right: str,
    prohibited: set[tuple[str, str]],
    all_record_ids: Iterable[str],
) -> bool:
    root_left, root_right = uf.find(left), uf.find(right)
    if root_left == root_right:
        return True
    left_members = component_members(uf, all_record_ids, root_left)
    right_members = component_members(uf, all_record_ids, root_right)
    return not any(
        tuple(sorted((a, b))) in prohibited
        for a in left_members for b in right_members
    )


def title_tokens(title_key: str) -> frozenset[str]:
    return frozenset(
        token for token in title_key.split()
        if len(token) >= 3 and token not in TITLE_STOPWORDS
    )


def token_jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
