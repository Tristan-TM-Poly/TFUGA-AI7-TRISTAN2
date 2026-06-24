from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .models import CVCDDigest, DigestDocument, OAKScore, Opportunity

QC_MARKERS = ("québec", "quebec", "montréal", "montreal", "laval", "sherbrooke", "gatineau", "rimouski", "qc")
DOMAINS = {
    "battery_energy": ("battery", "batterie", "impedance", "electrochemical", "energy", "lithium"),
    "photonics_mems": ("laser", "photon", "optical", "mems", "micro", "sensor"),
    "public_service_ai": ("public", "service", "administration", "graph", "workflow", "citizen"),
    "materials": ("material", "polymer", "alloy", "ceramic", "nanostructure"),
    "ai_automation": ("ai", "machine learning", "automation", "agent", "optimization"),
}
TRISTAN_BRANCHES = {
    "battery_energy": "Ω-BAT-T / Ω-ENERGY-T / FFWT-EIS",
    "photonics_mems": "Ω-LASER-MEMS-CPU-T / Ω-MFT-T",
    "public_service_ai": "Ω-PREUVE-T / AUTO² / OAK-Service-QC",
    "materials": "Ω-OEMMTD-T / Ω-TRANSFORM-T",
    "ai_automation": "Ω-AUTO²-T / SAGE/AIT",
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-") or "item"


def detect_domains(text: str) -> list[str]:
    t = text.casefold()
    return [name for name, words in DOMAINS.items() if any(w in t for w in words)] or ["general_research"]


def is_quebec_related(doc: DigestDocument) -> bool:
    haystack = " ".join([doc.title, doc.abstract, " ".join(doc.institutions), " ".join(doc.owners_or_assignees), " ".join(doc.authors_or_inventors)]).casefold()
    return any(marker in haystack for marker in QC_MARKERS)


def cvcd_digest(doc: DigestDocument) -> CVCDDigest:
    domains = detect_domains(doc.text())
    text = doc.text().casefold()
    problem = "map and exploit science-IP signals"
    method = "metadata and claim/abstract digestion"
    obj = ", ".join(domains)
    result = "candidate knowledge asset"
    evidence = "metadata only"
    limits = ["metadata-only digest", "requires human/OAK validation"]
    residue = []
    if doc.type == "patent":
        problem = "protect or exploit an invention claim"
        method = "claims and assignee analysis"
        evidence = "patent record, not functional proof"
        limits.append("not freedom-to-operate advice")
    if "impedance" in text or "battery" in text:
        result = "battery health signature candidate"
    if "laser" in text or "mems" in text:
        result = "laser/MEMS fabrication candidate"
    if "graph" in text and "service" in text:
        result = "public-service workflow intelligence candidate"
    if not is_quebec_related(doc):
        residue.append("weak Quebec signal")
    invariants = sorted(set(domains + [TRISTAN_BRANCHES.get(d, "OAK-general") for d in domains]))
    return CVCDDigest(doc.id, problem, method, obj, result, evidence, limits, invariants, residue)


def oak_score(doc: DigestDocument, digest: CVCDDigest) -> OAKScore:
    domains = detect_domains(doc.text())
    novelty = 0.62 if domains != ["general_research"] else 0.42
    evidence = 0.48 if doc.abstract else 0.22
    reproducibility = 0.36 if doc.type == "publication" else 0.18
    ip_risk = 0.58 if doc.type == "patent" else 0.32
    feasibility = 0.56 if any(d in domains for d in ("battery_energy", "photonics_mems", "public_service_ai")) else 0.38
    tristan_synergy = 0.72 if any(d in TRISTAN_BRANCHES for d in domains) else 0.44
    warnings = list(digest.limits + digest.residue)
    if doc.type == "patent":
        warnings.append("patent claims require legal-status/family review")
    if doc.type == "publication":
        warnings.append("publication requires method/data/code reproducibility check")
    return OAKScore(doc.id, novelty, evidence, reproducibility, ip_risk, feasibility, tristan_synergy, warnings)


def build_hypergraph(documents: Iterable[DigestDocument]) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    for doc in documents:
        nodes[doc.id] = {"id": doc.id, "type": doc.type, "label": doc.title}
        for domain in detect_domains(doc.text()):
            did = f"domain:{domain}"
            nodes.setdefault(did, {"id": did, "type": "domain", "label": domain})
            edges.append({"source": doc.id, "target": did, "type": "HAS_DOMAIN"})
        for inst in doc.institutions:
            iid = f"institution:{slug(inst)}"
            nodes.setdefault(iid, {"id": iid, "type": "institution", "label": inst})
            edges.append({"source": doc.id, "target": iid, "type": "AFFILIATED_WITH"})
        for owner in doc.owners_or_assignees:
            oid = f"owner:{slug(owner)}"
            nodes.setdefault(oid, {"id": oid, "type": "owner", "label": owner})
            edges.append({"source": doc.id, "target": oid, "type": "OWNED_BY"})
    return {"nodes": list(nodes.values()), "edges": edges}


def science_ip_bridges(documents: list[DigestDocument]) -> list[dict]:
    pubs = [d for d in documents if d.type == "publication"]
    patents = [d for d in documents if d.type == "patent"]
    bridges: list[dict] = []
    for pub in pubs:
        pdomains = set(detect_domains(pub.text()))
        for pat in patents:
            overlap = sorted(pdomains & set(detect_domains(pat.text())))
            if overlap:
                bridges.append({
                    "publication_id": pub.id,
                    "patent_id": pat.id,
                    "domains": overlap,
                    "confidence": round(0.45 + 0.15 * len(overlap), 2),
                    "oak_warning": "candidate bridge only; verify inventors, owners, dates, claims and prior art",
                })
    return bridges


def generate_opportunities(documents: list[DigestDocument], scores: dict[str, OAKScore]) -> list[Opportunity]:
    by_domain: dict[str, list[DigestDocument]] = defaultdict(list)
    for doc in documents:
        for domain in detect_domains(doc.text()):
            by_domain[domain].append(doc)
    opportunities: list[Opportunity] = []
    for domain, docs in sorted(by_domain.items()):
        mean_score = round(sum(scores[d.id].total for d in docs) / max(1, len(docs)), 3)
        branch = TRISTAN_BRANCHES.get(domain, "Ω-OAK-General")
        opportunities.append(Opportunity(
            id=f"opp-{domain}",
            name=f"{domain.replace('_', ' ').title()} Tristan bridge",
            domain=domain,
            score=mean_score,
            source_documents=[d.id for d in docs],
            prototype=f"Build {domain} OAKBench linked to {branch}",
            oak_next_test="verify sources, reproduce methods where possible, and run IP classification before disclosure",
            ip_strategy="internal_review_required; consider patent/trade-secret/open-publication classification",
            risks=["metadata false positives", "homonyms", "copyright/IP limits", "not legal advice"],
        ))
    return opportunities


def release_assessment(documents: list[DigestDocument], bridges: list[dict]) -> dict:
    patents = sum(d.type == "patent" for d in documents)
    pubs = sum(d.type == "publication" for d in documents)
    gates = {
        "OAK-Source": "pass_with_caution" if documents else "blocked",
        "OAK-IP": "review_required" if patents or bridges else "pass_with_caution",
        "OAK-Science": "review_required" if pubs else "pass_with_caution",
    }
    return {"gates": gates, "public_release": "draft_only", "reason": "science-IP outputs may contain patent-sensitive hypotheses"}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def render_report(documents: list[DigestDocument], opportunities: list[Opportunity], bridges: list[dict], assessment: dict) -> str:
    domains = Counter(d for doc in documents for d in detect_domains(doc.text()))
    lines = ["# Ω-SCI-PATENT-QC-DIGEST-T — PLUS ULTRA report", ""]
    lines.append(f"Documents: **{len(documents)}** | Opportunities: **{len(opportunities)}** | Bridges: **{len(bridges)}**")
    lines.append("")
    lines.append("## Gates")
    for k, v in assessment["gates"].items():
        lines.append(f"- **{k}**: `{v}`")
    lines.append("")
    lines.append("## Domains")
    for domain, count in domains.most_common():
        lines.append(f"- `{domain}`: {count}")
    lines.append("")
    lines.append("## Opportunities")
    for opp in opportunities:
        lines.append(f"### {opp.name}")
        lines.append(f"- Score: `{opp.score}`")
        lines.append(f"- Prototype: {opp.prototype}")
        lines.append(f"- OAK next test: {opp.oak_next_test}")
        lines.append("")
    return "\n".join(lines)


def run_pipeline(documents: list[DigestDocument], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    digests = {d.id: cvcd_digest(d) for d in documents}
    scores = {d.id: oak_score(d, digests[d.id]) for d in documents}
    graph = build_hypergraph(documents)
    bridges = science_ip_bridges(documents)
    opportunities = generate_opportunities(documents, scores)
    assessment = release_assessment(documents, bridges)
    write_json(out_dir / "documents.json", [d.to_dict() for d in documents])
    write_json(out_dir / "cvcd_digests.json", [d.to_dict() for d in digests.values()])
    write_json(out_dir / "oak_scores.json", [s.to_dict() for s in scores.values()])
    write_json(out_dir / "hypergraph.json", graph)
    write_json(out_dir / "bridges.json", bridges)
    write_json(out_dir / "opportunities.json", [o.to_dict() for o in opportunities])
    write_json(out_dir / "release_assessment.json", assessment)
    (out_dir / "PLUS_ULTRA_REPORT.md").write_text(render_report(documents, opportunities, bridges, assessment), encoding="utf-8")
    return {"documents": len(documents), "opportunities": len(opportunities), "bridges": len(bridges), "assessment": assessment}
