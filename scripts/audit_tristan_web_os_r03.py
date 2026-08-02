#!/usr/bin/env python3
"""Deterministic OAK audit for Tristan Web OS R0.3.

This audit checks structure, referential integrity, publication gates, negative-memory
visibility, application assets and offline-shell completeness. It does not certify
scientific truth, security, accessibility, legal status, IP status, or market value.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
DATA = SITE / "data"
GENERATED = ROOT / "content" / "generated"

EXPECTED = {"theories": 44, "claims": 133, "relations": 268}
OAK_KEYS = {"verite", "utilite", "testabilite", "simplicite", "valeur", "protection"}
GATE_KEYS = {"oak_gate", "ip_gate", "privacy_gate", "security_gate"}
APP_ASSETS = {
    "index.html", "app.js", "styles.css", "r03.css", "app.webmanifest", "sw.js",
    "src/application.js", "src/data-store.js", "src/exporters.js",
    "src/preferences.js", "src/router.js", "src/search-engine.js", "src/ui.js",
    "src/views/about.js", "src/views/atlas.js", "src/views/claims.js",
    "src/views/dashboard.js", "src/views/evidence.js", "src/views/graph.js",
    "src/views/mminus.js", "src/views/roadmap.js", "src/views/theory.js",
}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""
    object_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "object_id": self.object_id,
        }


@dataclass
class Audit:
    findings: list[Finding] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add(self, severity: str, code: str, message: str, *, path: str = "", object_id: str = "") -> None:
        self.findings.append(Finding(severity, code, message, path, object_id))

    def error(self, code: str, message: str, **kwargs: str) -> None:
        self.add("error", code, message, **kwargs)

    def warning(self, code: str, message: str, **kwargs: str) -> None:
        self.add("warning", code, message, **kwargs)

    def info(self, code: str, message: str, **kwargs: str) -> None:
        self.add("info", code, message, **kwargs)

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "error"]

    def report(self) -> dict[str, Any]:
        counts = Counter(item.severity for item in self.findings)
        return {
            "audit": "tristan-web-os-r03",
            "status": "fail" if self.errors else "pass",
            "metrics": self.metrics,
            "finding_counts": dict(counts),
            "findings": [item.to_dict() for item in self.findings],
            "epistemic_boundary": (
                "A passing audit confirms deterministic repository invariants only. "
                "It does not certify scientific truth, causality, security, accessibility, "
                "legal/IP status, safety, deployment readiness, or market value."
            ),
        }


def read_json(path: Path, audit: Audit) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        audit.error("file.missing", f"Missing JSON file: {path}", path=str(path.relative_to(ROOT)))
        return {}
    except json.JSONDecodeError as exc:
        audit.error("json.invalid", f"Invalid JSON: {exc}", path=str(path.relative_to(ROOT)))
        return {}
    if not isinstance(value, dict):
        audit.error("json.root", "JSON root must be an object", path=str(path.relative_to(ROOT)))
        return {}
    return value


def duplicates(values: Iterable[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def require_fields(audit: Audit, item: dict[str, Any], fields: set[str], *, object_id: str, path: str) -> None:
    missing = sorted(fields - set(item))
    if missing:
        audit.error("object.missing_fields", f"Missing fields: {', '.join(missing)}", object_id=object_id, path=path)


def audit_theories(audit: Audit, theories: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    path = "apps/tristan-8fire-site/data/theories.json"
    required = {
        "id", "symbol", "title", "summary", "domains", "maturity", "evidence",
        "artifacts", "oak", "status_note", "next_action", "source_path", "family",
        "claims_count", "version", "visibility", "risks", "publication", "links",
    }
    ids = [str(item.get("id", "")) for item in theories]
    for duplicate in sorted(duplicates(ids)):
        audit.error("theory.duplicate_id", f"Duplicate theory id {duplicate}", object_id=duplicate, path=path)
    index: dict[str, dict[str, Any]] = {}
    for item in theories:
        theory_id = str(item.get("id", "<missing>"))
        require_fields(audit, item, required, object_id=theory_id, path=path)
        index[theory_id] = item
        if not re.fullmatch(r"omega-[a-z0-9-]+", theory_id):
            audit.error("theory.id_format", "Theory id must use omega-kebab-case", object_id=theory_id, path=path)
        oak = item.get("oak")
        if not isinstance(oak, dict) or set(oak) != OAK_KEYS:
            audit.error("theory.oak_shape", f"OAK keys must equal {sorted(OAK_KEYS)}", object_id=theory_id, path=path)
        else:
            for key, value in oak.items():
                if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                    audit.error("theory.oak_range", f"OAK {key} outside [0,1]: {value}", object_id=theory_id, path=path)
        publication = item.get("publication")
        if not isinstance(publication, dict):
            audit.error("theory.publication_shape", "Publication block must be an object", object_id=theory_id, path=path)
        else:
            missing_gates = GATE_KEYS - set(publication)
            if missing_gates:
                audit.error("theory.gates_missing", f"Missing gates: {sorted(missing_gates)}", object_id=theory_id, path=path)
            if publication.get("automatic_external_action") is not False:
                audit.error("theory.external_action", "automatic_external_action must be false", object_id=theory_id, path=path)
        if not item.get("status_note") or not item.get("next_action"):
            audit.error("theory.oak_text", "Theory requires status_note and next_action", object_id=theory_id, path=path)
        if not item.get("risks"):
            audit.warning("theory.no_risk", "Theory declares no public risk tag", object_id=theory_id, path=path)
        routes = item.get("links", {})
        if routes.get("detail_route") != f"#/theory/{theory_id}":
            audit.error("theory.route", "Detail route does not match theory id", object_id=theory_id, path=path)
    return index


def audit_claims(audit: Audit, claims: list[dict[str, Any]], theories: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    path = "apps/tristan-8fire-site/data/claims.json"
    required = {
        "id", "theory_id", "kind", "title", "statement", "status", "epistemic_level",
        "confidence_label", "support", "counter_hypotheses", "falsification_or_limit",
        "next_test", "risk_tags", "publication_scope", "automatic_promotion", "updated_at",
    }
    ids = [str(item.get("id", "")) for item in claims]
    for duplicate in sorted(duplicates(ids)):
        audit.error("claim.duplicate_id", f"Duplicate claim id {duplicate}", object_id=duplicate, path=path)
    index: dict[str, dict[str, Any]] = {}
    counts = Counter()
    for item in claims:
        claim_id = str(item.get("id", "<missing>"))
        require_fields(audit, item, required, object_id=claim_id, path=path)
        index[claim_id] = item
        theory_id = str(item.get("theory_id", ""))
        counts[theory_id] += 1
        if theory_id not in theories:
            audit.error("claim.orphan", f"Unknown theory_id {theory_id}", object_id=claim_id, path=path)
        if item.get("automatic_promotion") is not False:
            audit.error("claim.auto_promotion", "automatic_promotion must be false", object_id=claim_id, path=path)
        if not item.get("support"):
            audit.error("claim.no_support", "Claim requires at least one declared support", object_id=claim_id, path=path)
        if not item.get("counter_hypotheses"):
            audit.error("claim.no_counter", "Claim requires at least one counter-hypothesis", object_id=claim_id, path=path)
        if len(str(item.get("falsification_or_limit", ""))) < 15:
            audit.error("claim.no_limit", "Claim requires a substantive limit or falsification condition", object_id=claim_id, path=path)
        if len(str(item.get("next_test", ""))) < 15:
            audit.error("claim.no_test", "Claim requires a substantive next test", object_id=claim_id, path=path)
    for theory_id, theory in theories.items():
        declared = int(theory.get("claims_count", -1))
        actual = counts[theory_id]
        if declared != actual:
            audit.error("claim.count_mismatch", f"Declared {declared}, actual {actual}", object_id=theory_id, path=path)
    return index


def audit_relations(audit: Audit, relations: list[dict[str, Any]], theories: dict[str, dict[str, Any]]) -> None:
    path = "apps/tristan-8fire-site/data/relations.json"
    required = {"id", "source", "target", "kind", "rationale", "strength", "status", "directional", "evidence_required", "public_scope"}
    ids = [str(item.get("id", "")) for item in relations]
    for duplicate in sorted(duplicates(ids)):
        audit.error("relation.duplicate_id", f"Duplicate relation id {duplicate}", object_id=duplicate, path=path)
    seen_pairs: set[tuple[str, str, str]] = set()
    for item in relations:
        relation_id = str(item.get("id", "<missing>"))
        require_fields(audit, item, required, object_id=relation_id, path=path)
        source = str(item.get("source", ""))
        target = str(item.get("target", ""))
        kind = str(item.get("kind", ""))
        if source not in theories or target not in theories:
            audit.error("relation.orphan", f"Unknown endpoint {source} -> {target}", object_id=relation_id, path=path)
        if source == target:
            audit.error("relation.self_loop", "Public navigation relation may not be a self-loop", object_id=relation_id, path=path)
        pair = (source, target, kind)
        if pair in seen_pairs:
            audit.warning("relation.duplicate_semantic", f"Repeated relation {pair}", object_id=relation_id, path=path)
        seen_pairs.add(pair)
        strength = item.get("strength")
        if not isinstance(strength, (int, float)) or not 0 <= float(strength) <= 1:
            audit.error("relation.strength", f"Strength outside [0,1]: {strength}", object_id=relation_id, path=path)
        if item.get("evidence_required") is not True:
            audit.error("relation.evidence_required", "evidence_required must be true", object_id=relation_id, path=path)
        if item.get("public_scope") != "navigation":
            audit.error("relation.public_scope", "public_scope must remain navigation", object_id=relation_id, path=path)


def audit_application(audit: Audit) -> None:
    for relative in sorted(APP_ASSETS):
        path = SITE / relative
        if not path.is_file():
            audit.error("app.asset_missing", f"Missing application asset {relative}", path=str(path.relative_to(ROOT)))
        elif path.stat().st_size < 20:
            audit.error("app.asset_empty", f"Application asset too small {relative}", path=str(path.relative_to(ROOT)))
    index = (SITE / "index.html").read_text(encoding="utf-8") if (SITE / "index.html").exists() else ""
    for token in ["#/dashboard", "#/atlas", "#/claims", "#/graph", "#/evidence", "#/mminus", "#/roadmap", "#/about"]:
        if token not in index:
            audit.error("app.route_missing", f"Navigation token missing: {token}", path="apps/tristan-8fire-site/index.html")
    if 'type="module"' not in index:
        audit.error("app.module_boot", "app.js must load as an ES module", path="apps/tristan-8fire-site/index.html")
    app = (SITE / "src" / "application.js").read_text(encoding="utf-8") if (SITE / "src" / "application.js").exists() else ""
    for route in ["dashboard", "atlas", "theory", "claims", "claim", "graph", "evidence", "mminus", "roadmap", "about"]:
        if f"{route}:" not in app:
            audit.error("app.renderer_missing", f"Renderer not registered: {route}", path="apps/tristan-8fire-site/src/application.js")
    worker = (SITE / "sw.js").read_text(encoding="utf-8") if (SITE / "sw.js").exists() else ""
    for required in ["data/theories.json", "data/claims.json", "data/relations.json"]:
        if required not in worker:
            audit.error("app.offline_data", f"Service worker missing {required}", path="apps/tristan-8fire-site/sw.js")


def audit_generated(audit: Audit, theories: list[dict[str, Any]]) -> None:
    cards = sorted((GENERATED / "theory-cards").glob("*.md")) if (GENERATED / "theory-cards").exists() else []
    if len(cards) != len(theories):
        audit.error("generated.card_count", f"Expected {len(theories)} cards, got {len(cards)}", path="content/generated/theory-cards")
    for required in ["CATALOG_SUMMARY.md", "CLAIM_INDEX.md", "RELATION_INDEX.md"]:
        if not (GENERATED / required).is_file():
            audit.error("generated.index_missing", f"Missing generated index {required}", path=f"content/generated/{required}")


def run_audit() -> Audit:
    audit = Audit()
    theory_payload = read_json(DATA / "theories.json", audit)
    claim_payload = read_json(DATA / "claims.json", audit)
    relation_payload = read_json(DATA / "relations.json", audit)
    theories = theory_payload.get("theories", []) if isinstance(theory_payload.get("theories", []), list) else []
    claims = claim_payload.get("claims", []) if isinstance(claim_payload.get("claims", []), list) else []
    relations = relation_payload.get("relations", []) if isinstance(relation_payload.get("relations", []), list) else []
    audit.metrics.update({"theories": len(theories), "claims": len(claims), "relations": len(relations)})
    for key, expected in EXPECTED.items():
        actual = audit.metrics[key]
        if actual != expected:
            audit.error("catalog.count", f"Expected {expected} {key}, got {actual}", path=f"apps/tristan-8fire-site/data/{key}.json")
    theory_index = audit_theories(audit, theories)
    audit_claims(audit, claims, theory_index)
    audit_relations(audit, relations, theory_index)
    audit_application(audit)
    audit_generated(audit, theories)
    audit.metrics["publication_ready"] = sum(
        1 for item in theories if all(item.get("publication", {}).get(key) is True for key in GATE_KEYS)
    )
    audit.metrics["automatic_external_actions"] = sum(
        1 for item in theories if item.get("publication", {}).get("automatic_external_action") is not False
    )
    audit.metrics["automatic_claim_promotions"] = sum(1 for item in claims if item.get("automatic_promotion") is not False)
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    parser.add_argument("--strict-warnings", action="store_true", help="Fail when warnings are present")
    args = parser.parse_args(argv)
    audit = run_audit()
    report = audit.report()
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    if audit.errors:
        return 1
    if args.strict_warnings and any(item.severity == "warning" for item in audit.findings):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
