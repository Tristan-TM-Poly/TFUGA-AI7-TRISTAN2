"""Ω-PROTOTYPE-PORTFOLIO-T∞ R0.1 MAX.

Deterministic, dependency-light portfolio intelligence for Tristan prototypes.
Scores are routing heuristics, never truth probabilities or market valuations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.sax.saxutils import escape

DIMENSIONS = (
    "truth", "code", "tests", "baseline", "product", "user", "ip",
    "github", "revenue", "risk_control", "documentation", "reproducibility",
    "external_validation", "integration", "maintainability", "novelty",
    "utility", "falsifiability",
)
SIGNALS = (
    "ci_green", "cli_available", "schema_available", "deterministic",
    "m_minus_available", "real_data", "independent_reproduction",
    "external_user", "payment_collected", "repeat_usage", "retention",
    "release_published",
)
STAGE_ORDER = ("P0_IDEA", "P1_STRUCTURED", "P2_EXECUTABLE", "P3_TESTED", "P4_BENCHMARKED", "P5_EXTERNAL", "P6_PRODUCT", "P7_RETAINED", "P8_CANON")
EVIDENCE_STRENGTH = {"DECLARED": 0, "OBSERVED": 1, "REPRODUCED": 2, "INDEPENDENT": 3}
RELATIONS = {"depends_on", "overlaps", "supersedes", "derived_from", "complements", "blocks"}
CATEGORIES = {"science", "mathematics", "infrastructure", "product", "operations", "theory"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _score(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
        raise ValueError(f"{name} must be an integer in 0..5")
    return value


@dataclass(frozen=True)
class Evidence:
    kind: str
    reference: str
    strength: str = "OBSERVED"
    note: str = ""
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.kind.strip() or not self.reference.strip():
            raise ValueError("evidence kind and reference are required")
        if self.strength not in EVIDENCE_STRENGTH:
            raise ValueError(f"unknown evidence strength: {self.strength}")
        if self.sha256 is not None and (len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256)):
            raise ValueError("sha256 must be lowercase 64-hex")


@dataclass(frozen=True)
class ClaimBoundary:
    status: str
    claim: str
    certified: bool = False
    independent: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"speculative", "structured", "executable", "tested", "benchmarked", "externally_observed", "product_observed", "retained", "canonical"}:
            raise ValueError(f"unknown claim status: {self.status}")
        if not self.claim.strip():
            raise ValueError("claim cannot be empty")
        if self.certified and self.status in {"speculative", "structured", "executable"}:
            raise ValueError("early-stage claims cannot be certified")


@dataclass(frozen=True)
class Relation:
    kind: str
    target_id: str
    note: str = ""

    def __post_init__(self) -> None:
        if self.kind not in RELATIONS:
            raise ValueError(f"unknown relation: {self.kind}")
        if not self.target_id.strip():
            raise ValueError("relation target_id is required")


@dataclass(frozen=True)
class NextAction:
    title: str
    kind: str
    effort_hours: int
    expected_evidence: str
    external: bool = False

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.expected_evidence.strip():
            raise ValueError("next action title and evidence are required")
        if self.kind not in {"test", "benchmark", "integration", "documentation", "release", "user", "market", "science", "ip", "archive"}:
            raise ValueError(f"unknown action kind: {self.kind}")
        if not 1 <= self.effort_hours <= 200:
            raise ValueError("effort_hours must be in 1..200")


@dataclass(frozen=True)
class Prototype:
    prototype_id: str
    name: str
    category: str
    repository: str
    ref: str
    summary: str
    dimensions: Mapping[str, int]
    signals: Mapping[str, bool]
    evidence: tuple[Evidence, ...]
    claim: ClaimBoundary
    risks: tuple[str, ...]
    next_action: NextAction
    relations: tuple[Relation, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.prototype_id.strip() or not self.name.strip() or not self.repository.strip() or not self.ref.strip():
            raise ValueError("prototype identity, name, repository and ref are required")
        if self.category not in CATEGORIES:
            raise ValueError(f"unknown category: {self.category}")
        unknown_dimensions = set(self.dimensions) - set(DIMENSIONS)
        unknown_signals = set(self.signals) - set(SIGNALS)
        if unknown_dimensions or unknown_signals:
            raise ValueError(f"unknown fields: {sorted(unknown_dimensions | unknown_signals)}")
        for name in DIMENSIONS:
            _score(int(self.dimensions.get(name, 0)), name)
        for name in SIGNALS:
            if not isinstance(self.signals.get(name, False), bool):
                raise ValueError(f"signal {name} must be boolean")
        if not self.evidence:
            raise ValueError("prototype requires evidence")
        if self.signals.get("retention", False) and not self.signals.get("repeat_usage", False):
            raise ValueError("retention requires repeat_usage")
        if self.signals.get("repeat_usage", False) and not self.signals.get("payment_collected", False):
            raise ValueError("repeat_usage requires collected payment in R0.1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    observed_at: str
    source_heads: Mapping[str, str]
    prototypes: tuple[Prototype, ...]
    policy_version: str = "r0.1"
    external_action_performed: bool = False
    truth_probability_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip() or not self.observed_at.strip():
            raise ValueError("snapshot identity and observed_at are required")
        if self.external_action_performed or self.truth_probability_claimed:
            raise ValueError("R0.1 snapshots are review-only and cannot claim truth probability")
        ids = [item.prototype_id for item in self.prototypes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate prototype IDs")
        for repo, sha in self.source_heads.items():
            if not repo.strip() or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
                raise ValueError("source heads require repository and lowercase 40-hex SHA")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def sha256(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True)
class Assessment:
    prototype_id: str
    stage: str
    maturity: float
    science: float
    engineering: float
    product: float
    integration: float
    evidence_density: float
    externalization: float
    priority: float
    risk_debt: float
    blockers: tuple[str, ...]
    m_minus: tuple[str, ...]
    next_action: NextAction

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _avg(record: Prototype, names: Sequence[str]) -> float:
    return round(sum(record.dimensions.get(name, 0) for name in names) / len(names), 3)


def _stage(record: Prototype) -> tuple[str, list[str]]:
    d, s = record.dimensions, record.signals
    stage, blockers = "P0_IDEA", []
    if d.get("documentation", 0) >= 2 and d.get("truth", 0) >= 1:
        stage = "P1_STRUCTURED"
    else:
        blockers.append("structured_definition_missing")
        return stage, blockers
    if d.get("code", 0) >= 2 and s.get("cli_available", False):
        stage = "P2_EXECUTABLE"
    else:
        blockers.append("executable_kernel_or_cli_missing")
        return stage, blockers
    if d.get("tests", 0) >= 2 and s.get("ci_green", False):
        stage = "P3_TESTED"
    else:
        blockers.append("tests_or_exact_head_ci_missing")
        return stage, blockers
    if d.get("baseline", 0) >= 2 and d.get("falsifiability", 0) >= 3:
        stage = "P4_BENCHMARKED"
    else:
        blockers.append("baseline_or_falsification_missing")
        return stage, blockers
    if s.get("real_data", False) or s.get("independent_reproduction", False) or s.get("external_user", False):
        stage = "P5_EXTERNAL"
    else:
        blockers.append("external_evidence_missing")
        return stage, blockers
    if s.get("payment_collected", False) and d.get("product", 0) >= 3:
        stage = "P6_PRODUCT"
    else:
        blockers.append("collected_payment_or_product_evidence_missing")
        return stage, blockers
    if s.get("repeat_usage", False) and s.get("retention", False):
        stage = "P7_RETAINED"
    else:
        blockers.append("repeat_usage_or_retention_missing")
        return stage, blockers
    if record.claim.independent and record.claim.certified and d.get("maintainability", 0) >= 4:
        stage = "P8_CANON"
    else:
        blockers.append("independent_certification_or_maintainability_missing")
    return stage, blockers


def assess(record: Prototype) -> Assessment:
    stage, blockers = _stage(record)
    maturity = round(STAGE_ORDER.index(stage) / (len(STAGE_ORDER) - 1) * 100, 2)
    science = _avg(record, ("truth", "baseline", "external_validation", "reproducibility", "falsifiability")) * 20
    engineering = _avg(record, ("code", "tests", "github", "documentation", "maintainability")) * 20
    product = _avg(record, ("product", "user", "revenue", "utility")) * 20
    integration = _avg(record, ("integration", "github", "documentation", "maintainability")) * 20
    strongest = max(EVIDENCE_STRENGTH[e.strength] for e in record.evidence)
    evidence_density = round(min(100.0, len(record.evidence) * 8 + strongest * 18 + record.dimensions.get("reproducibility", 0) * 5), 2)
    externalization = round((science * 0.35 + product * 0.35 + integration * 0.2 + evidence_density * 0.1), 2)
    risk_debt = round((5 - record.dimensions.get("risk_control", 0)) * 12 + len(record.risks) * 4 + len(blockers) * 3, 2)
    priority = round(max(0.0, 0.22 * science + 0.2 * engineering + 0.25 * product + 0.18 * integration + 0.15 * evidence_density - 0.35 * risk_debt), 2)
    m_minus: list[str] = []
    if engineering >= 70 and externalization < 60:
        m_minus.append("M-PROTOTYPE-INTERNAL-STRENGTH-EXTERNAL-GAP")
    if record.dimensions.get("code", 0) >= 4 and record.dimensions.get("tests", 0) < 2:
        m_minus.append("M-CODE-OUTRUNS-TESTS")
    if record.dimensions.get("product", 0) >= 3 and not record.signals.get("external_user", False):
        m_minus.append("M-PRODUCT-WITHOUT-USER")
    if record.signals.get("payment_collected", False) and not record.signals.get("retention", False):
        m_minus.append("M-PAYMENT-NOT-RETENTION")
    if len(record.relations) >= 3 and record.dimensions.get("integration", 0) < 3:
        m_minus.append("M-HIGH-COUPLING-LOW-INTEGRATION")
    return Assessment(record.prototype_id, stage, maturity, round(science, 2), round(engineering, 2), round(product, 2), round(integration, 2), evidence_density, externalization, priority, risk_debt, tuple(blockers), tuple(m_minus), record.next_action)


def audit(snapshot: Snapshot) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    ids = {p.prototype_id for p in snapshot.prototypes}
    for p in snapshot.prototypes:
        for rel in p.relations:
            if rel.target_id not in ids:
                findings.append({"severity": "error", "code": "MISSING_RELATION_TARGET", "prototype_id": p.prototype_id, "detail": rel.target_id})
        if p.claim.certified and max(EVIDENCE_STRENGTH[e.strength] for e in p.evidence) < 2:
            findings.append({"severity": "error", "code": "CERTIFICATION_WITHOUT_REPRODUCED_EVIDENCE", "prototype_id": p.prototype_id, "detail": p.claim.status})
        if p.signals.get("ci_green", False) and not any(e.kind in {"ci", "test"} for e in p.evidence):
            findings.append({"severity": "error", "code": "CI_SIGNAL_WITHOUT_EVIDENCE", "prototype_id": p.prototype_id, "detail": "ci_green"})
    cycles = dependency_cycles(snapshot)
    for cycle in cycles:
        findings.append({"severity": "error", "code": "DEPENDENCY_CYCLE", "prototype_id": cycle[0], "detail": " -> ".join(cycle)})
    status = "PASS" if not any(f["severity"] == "error" for f in findings) else "FAIL"
    report = {"status": status, "snapshot_sha256": snapshot.sha256, "prototype_count": len(snapshot.prototypes), "finding_count": len(findings), "findings": findings, "external_action_performed": False, "truth_probability_claimed": False}
    report["report_sha256"] = digest(report)
    return report


def dependency_cycles(snapshot: Snapshot) -> list[list[str]]:
    graph = {p.prototype_id: [r.target_id for r in p.relations if r.kind == "depends_on"] for p in snapshot.prototypes}
    visiting: set[str] = set(); visited: set[str] = set(); cycles: list[list[str]] = []
    def walk(node: str, path: list[str]) -> None:
        if node in visiting:
            start = path.index(node)
            cycles.append(path[start:] + [node]); return
        if node in visited: return
        visiting.add(node)
        for target in graph.get(node, []):
            if target in graph: walk(target, path + [target])
        visiting.remove(node); visited.add(node)
    for node in sorted(graph): walk(node, [node])
    unique: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in cycles:
        key = tuple(cycle)
        if key not in seen: seen.add(key); unique.append(cycle)
    return unique


def graphml(snapshot: Snapshot) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">', '<graph id="prototype-portfolio" edgedefault="directed">']
    for p in sorted(snapshot.prototypes, key=lambda x: x.prototype_id):
        lines.append(f'<node id="{escape(p.prototype_id)}"><data key="name">{escape(p.name)}</data><data key="category">{escape(p.category)}</data></node>')
    edge_no = 0
    for p in sorted(snapshot.prototypes, key=lambda x: x.prototype_id):
        for rel in sorted(p.relations, key=lambda x: (x.kind, x.target_id)):
            lines.append(f'<edge id="e{edge_no}" source="{escape(p.prototype_id)}" target="{escape(rel.target_id)}"><data key="kind">{escape(rel.kind)}</data></edge>'); edge_no += 1
    lines.extend(["</graph>", "</graphml>"])
    return "\n".join(lines) + "\n"


def analyze(snapshot: Snapshot) -> dict[str, Any]:
    assessments = [assess(p) for p in snapshot.prototypes]
    ranked = sorted(assessments, key=lambda x: (-x.priority, x.prototype_id))
    stage_counts = {stage: sum(a.stage == stage for a in assessments) for stage in STAGE_ORDER}
    repo_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for p in snapshot.prototypes:
        repo_counts[p.repository] = repo_counts.get(p.repository, 0) + 1
        category_counts[p.category] = category_counts.get(p.category, 0) + 1
    result = {"snapshot_id": snapshot.snapshot_id, "snapshot_sha256": snapshot.sha256, "prototype_count": len(snapshot.prototypes), "stage_counts": stage_counts, "repository_counts": dict(sorted(repo_counts.items())), "category_counts": dict(sorted(category_counts.items())), "assessments": [a.to_dict() for a in ranked], "m_minus": sorted({m for a in assessments for m in a.m_minus}), "dependency_cycles": dependency_cycles(snapshot), "external_action_performed": False, "truth_probability_claimed": False}
    result["analysis_sha256"] = digest(result)
    return result


def plan(snapshot: Snapshot, max_items: int = 6, max_hours: int = 40, max_per_category: int = 2, max_per_repository: int = 3) -> dict[str, Any]:
    if min(max_items, max_hours, max_per_category, max_per_repository) < 1:
        raise ValueError("planning budgets must be positive")
    records = {p.prototype_id: p for p in snapshot.prototypes}
    candidates = sorted((assess(p) for p in snapshot.prototypes), key=lambda a: (-a.priority, a.next_action.effort_hours, a.prototype_id))
    selected: list[dict[str, Any]] = []; used_hours = 0; category_use: dict[str, int] = {}; repo_use: dict[str, int] = {}
    for a in candidates:
        p = records[a.prototype_id]
        if len(selected) >= max_items or used_hours + a.next_action.effort_hours > max_hours: continue
        if category_use.get(p.category, 0) >= max_per_category or repo_use.get(p.repository, 0) >= max_per_repository: continue
        selected.append({"prototype_id": p.prototype_id, "name": p.name, "category": p.category, "repository": p.repository, "stage": a.stage, "priority": a.priority, "action": asdict(a.next_action), "blockers": list(a.blockers), "external_action_authorized": False})
        used_hours += a.next_action.effort_hours; category_use[p.category] = category_use.get(p.category, 0) + 1; repo_use[p.repository] = repo_use.get(p.repository, 0) + 1
    result = {"snapshot_sha256": snapshot.sha256, "budget": {"max_items": max_items, "max_hours": max_hours, "max_per_category": max_per_category, "max_per_repository": max_per_repository, "permanent_total_cap": None}, "selected_count": len(selected), "used_hours": used_hours, "selected": selected, "external_action_performed": False, "merge_authorized": False, "publication_authorized": False}
    result["plan_sha256"] = digest(result)
    return result


def markdown(snapshot: Snapshot, analysis: Mapping[str, Any], portfolio_plan: Mapping[str, Any]) -> str:
    by_id = {p.prototype_id: p for p in snapshot.prototypes}
    lines = ["# Ω-PROTOTYPE-PORTFOLIO-T∞ R0.1", "", f"Snapshot: `{snapshot.snapshot_id}`", f"Digest: `{snapshot.sha256}`", "", "## Portfolio", "", "| Rank | Prototype | Stage | Science | Engineering | Product | Priority |", "|---:|---|---|---:|---:|---:|---:|"]
    for i, a in enumerate(analysis["assessments"], 1):
        p = by_id[a["prototype_id"]]
        lines.append(f"| {i} | {p.name} | {a['stage']} | {a['science']:.1f} | {a['engineering']:.1f} | {a['product']:.1f} | {a['priority']:.1f} |")
    lines.extend(["", "## Crystallization plan", ""])
    for item in portfolio_plan["selected"]:
        lines.append(f"- **{item['name']}** — {item['action']['title']} ({item['action']['effort_hours']} h); evidence: {item['action']['expected_evidence']}.")
    lines.extend(["", "## OAK boundaries", "", "- score != probability of truth", "- CI green != independent scientific validation", "- logical frontier != executed evidence", "- invoice != payment; payment != retention", "- no merge, publication, deployment, external send or spending authority", ""])
    return "\n".join(lines)


def compile_bundle(snapshot: Snapshot, output_dir: str | Path, *, max_items: int = 6, max_hours: int = 40) -> dict[str, str]:
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    analysis = analyze(snapshot); portfolio_plan = plan(snapshot, max_items=max_items, max_hours=max_hours); audit_report = audit(snapshot)
    payloads: dict[str, str] = {
        "snapshot.json": json.dumps(snapshot.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "assessments.jsonl": "".join(json.dumps(a, ensure_ascii=False, sort_keys=True) + "\n" for a in analysis["assessments"]),
        "analysis.json": json.dumps(analysis, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "plan.json": json.dumps(portfolio_plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "audit.json": json.dumps(audit_report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "portfolio.graphml": graphml(snapshot),
        "REPORT.md": markdown(snapshot, analysis, portfolio_plan),
        "m_minus.jsonl": "".join(json.dumps({"code": code, "snapshot_sha256": snapshot.sha256}, sort_keys=True) + "\n" for code in analysis["m_minus"]),
    }
    receipts = {name: hashlib.sha256(content.encode("utf-8")).hexdigest() for name, content in payloads.items()}
    manifest = {"snapshot_sha256": snapshot.sha256, "files": receipts, "external_action_performed": False, "truth_probability_claimed": False}
    manifest["manifest_sha256"] = digest(manifest); payloads["manifest.json"] = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    for name, content in payloads.items(): (root / name).write_text(content, encoding="utf-8")
    return {name: hashlib.sha256(content.encode("utf-8")).hexdigest() for name, content in payloads.items()}


def compare(left: Snapshot, right: Snapshot) -> dict[str, Any]:
    l = {p.prototype_id: p for p in left.prototypes}; r = {p.prototype_id: p for p in right.prototypes}
    added = sorted(set(r) - set(l)); removed = sorted(set(l) - set(r)); changed = sorted(k for k in set(l) & set(r) if digest(l[k].to_dict()) != digest(r[k].to_dict()))
    result = {"left_sha256": left.sha256, "right_sha256": right.sha256, "added": added, "removed": removed, "changed": changed, "unchanged_count": len(set(l) & set(r)) - len(changed)}; result["delta_sha256"] = digest(result); return result


def prototype_from_dict(data: Mapping[str, Any]) -> Prototype:
    return Prototype(
        prototype_id=data["prototype_id"], name=data["name"], category=data["category"], repository=data["repository"], ref=data["ref"], summary=data["summary"],
        dimensions={k: int(v) for k, v in data["dimensions"].items()}, signals={k: bool(v) for k, v in data["signals"].items()},
        evidence=tuple(Evidence(**e) for e in data["evidence"]), claim=ClaimBoundary(**{**data["claim"], "limitations": tuple(data["claim"].get("limitations", ())) }),
        risks=tuple(data.get("risks", ())), next_action=NextAction(**data["next_action"]), relations=tuple(Relation(**rel) for rel in data.get("relations", ())), tags=tuple(data.get("tags", ())),
    )


def snapshot_from_dict(data: Mapping[str, Any]) -> Snapshot:
    return Snapshot(snapshot_id=data["snapshot_id"], observed_at=data["observed_at"], source_heads=dict(data["source_heads"]), prototypes=tuple(prototype_from_dict(p) for p in data["prototypes"]), policy_version=data.get("policy_version", "r0.1"), external_action_performed=bool(data.get("external_action_performed", False)), truth_probability_claimed=bool(data.get("truth_probability_claimed", False)))


def load_snapshot(path: str | Path) -> Snapshot:
    return snapshot_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
