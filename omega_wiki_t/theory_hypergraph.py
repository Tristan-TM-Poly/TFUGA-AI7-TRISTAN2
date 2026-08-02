from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence
from xml.sax.saxutils import escape, quoteattr


_ALIAS_LABELS = {
    "dct++": "DCT-Ω / DCT++",
    "dct-ω": "DCT-Ω / DCT++",
    "dct-omega": "DCT-Ω / DCT++",
    "ai-7 production-verification metabolism": "AI-7",
    "ai-7 production-verification metabolism.": "AI-7",
    "ω-deeptech intelligence forge": "Ω-DeepTech Intelligence Forge",
    "omega-deeptech intelligence forge": "Ω-DeepTech Intelligence Forge",
    "company revenue ip publication os": "Company Revenue IP Publication OS",
    "failuresynth and memory-negative engine": "FailureSynth",
}

_LAYER_DOMAIN = {
    "pre-axiomatic core": "foundations",
    "mathematical core": "mathematics",
    "physics conjectures": "physics",
    "ait systems": "ait",
    "prototypes and impact systems": "prototype",
}

_CORE_RELATIONS: tuple[tuple[str, str, tuple[str, ...], float, str], ...] = (
    ("rel-core-001", "root_generates_representation", ("TFUGA", "HGFM"), 0.95, "TFUGA is the generative root and HGFM its hypergraph representation layer."),
    ("rel-core-002", "representation_supports_compression", ("HGFM", "CVCD"), 0.90, "HGFM organizes objects and relations that CVCD compresses and selectively expands."),
    ("rel-core-003", "verification_governs", ("OAK", "TFUGA", "HGFM", "CVCD"), 0.96, "OAK gates definitions, tests, residues, and promotion across the core theory stack."),
    ("rel-core-004", "evidence_contract_operationalizes", ("DCT-Ω / DCT++", "OAK"), 0.92, "DCT-Ω/DCT++ packages document, code, tests, data, risk, ethics, status, next action, and links."),
    ("rel-core-005", "posterior_calibration", ("Bayes-Tristan", "OAK"), 0.86, "Bayes-Tristan supplies posterior decision structure while OAK prevents fertility from being confused with proof."),
    ("rel-core-006", "signal_branch_specializes", ("FFWT-HAC-CVCD", "CVCD", "HGFM"), 0.88, "The FFWT branch applies multiscale compression and hypergraph coherence to signals and spectroscopy."),
    ("rel-core-007", "negative_memory_feedback", ("FailureSynth", "OAK"), 0.84, "FailureSynth converts errors and refutations into reusable negative memory for later gates."),
    ("rel-core-008", "workflow_compiler_governed_by", ("AUTO² Kernel", "OAK"), 0.90, "AUTO² compiles workflows with forbidden actions, rollback, and telemetry under OAK constraints."),
    ("rel-core-009", "benchmark_governed_by", ("Ω-LIN-T", "OAK"), 0.91, "Ω-LIN-T is a locally demonstrated OAKBench with residuals and validity domains."),
    ("rel-core-010", "deeptech_routes_value", ("Ω-DeepTech Intelligence Forge", "Company Revenue IP Publication OS", "OAK"), 0.90, "DeepTech Forge routes evidence-ranked signals toward IP, revenue, publication, and prototypes behind OAK review."),
    ("rel-core-011", "publication_requires_review", ("Publication Atlas", "OAK"), 0.83, "Publication matching remains metadata until human review and evidence checks."),
    ("rel-core-012", "data_ingestion_requires_license_gate", ("Open Data Harvester", "OAK"), 0.84, "Open-data retrieval must preserve licensing, provenance, and bounded access."),
    ("rel-core-013", "recursive_generation_uses_representation", ("AIT-Universe", "HGFM", "OAK"), 0.82, "Recursive node expansion uses HGFM while OAK limits unbounded recursion and false promotion."),
    ("rel-core-014", "production_verification_metabolism", ("AI-7", "OAK", "DCT-Ω / DCT++"), 0.91, "AI-7 couples production, verification, testing, integration, and canonization through explicit evidence packets."),
)


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{sha256(raw).hexdigest()[:20]}"


def normalize_label(raw: str) -> str:
    text = raw.strip().strip("`*_ ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.$", "", text)
    return _ALIAS_LABELS.get(text.casefold(), text)


def node_key(label: str) -> str:
    text = normalize_label(label).casefold().replace("ω", "omega")
    text = re.sub(r"[^a-z0-9à-öø-ÿ]+", "-", text)
    return text.strip("-")


def _status_score(status: str) -> float:
    lowered = status.casefold()
    if "canonical" in lowered or re.search(r"(^|/)c($|/)", lowered):
        return 0.90
    if "core safety" in lowered:
        return 0.88
    if "high-priority" in lowered:
        return 0.84
    if "operational" in lowered or "d-mvp" in lowered or re.search(r"(^|/)d($|/)", lowered):
        return 0.80
    if "active" in lowered:
        return 0.72
    if "x" == lowered.strip() or "x/" in lowered or "/x" in lowered or "crystallizable" in lowered:
        return 0.64
    if "exploratory" in lowered or lowered.startswith("e"):
        return 0.48
    if lowered.startswith("s") or "speculative" in lowered:
        return 0.30
    return 0.50


def utility_score(status: str, rank: int | None, next_action: str, role: str) -> float:
    score = _status_score(status)
    if rank is not None and rank > 0:
        score += max(0.0, 0.14 * (14 - min(rank, 14)) / 13)
    if next_action.strip():
        score += 0.04
    if any(token in role.casefold() for token in ("test", "prototype", "executable", "benchmark", "reusable")):
        score += 0.03
    return round(min(1.0, score), 3)


@dataclass(frozen=True)
class TheoryNode:
    node_id: str
    label: str
    kind: str = "theory_system"
    domain: str = "cross-domain"
    oak_status: str = "unclassified"
    role: str = ""
    risk: str = ""
    next_action: str = ""
    rank: int | None = None
    utility_score: float = 0.5
    source_paths: tuple[str, ...] = ()
    evidence_class: str = "repository_canon_extraction"


@dataclass(frozen=True)
class KnowledgeHyperedge:
    edge_id: str
    kind: str
    node_ids: tuple[str, ...]
    weight: float
    rationale: str
    evidence_paths: tuple[str, ...]
    status: str = "candidate_relation_from_canon"


@dataclass
class TheoryHypergraph:
    nodes: list[TheoryNode] = field(default_factory=list)
    hyperedges: list[KnowledgeHyperedge] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest,
            "nodes": [asdict(node) for node in self.nodes],
            "hyperedges": [asdict(edge) for edge in self.hyperedges],
        }

    def validate(self) -> list[str]:
        issues: list[str] = []
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            issues.append("duplicate node ids")
        edge_ids = [edge.edge_id for edge in self.hyperedges]
        if len(edge_ids) != len(set(edge_ids)):
            issues.append("duplicate hyperedge ids")
        known = set(node_ids)
        for edge in self.hyperedges:
            missing = sorted(set(edge.node_ids) - known)
            if missing:
                issues.append(f"{edge.edge_id}: missing nodes {missing}")
            if len(edge.node_ids) < 2:
                issues.append(f"{edge.edge_id}: hyperedge has fewer than two nodes")
        return issues


class TheoryHypergraphBuilder:
    """Build a traceable knowledge hypergraph from Tristan repository canon files.

    This repository-theory bridge for WikiForge-T does not certify the
    underlying theories. It preserves source paths, OAK status, risks, next
    actions, and a transparent usefulness heuristic for navigation and tests.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, TheoryNode] = {}
        self._edges: dict[str, KnowledgeHyperedge] = {}

    def _upsert_node(
        self,
        label: str,
        *,
        kind: str = "theory_system",
        domain: str = "cross-domain",
        oak_status: str = "unclassified",
        role: str = "",
        risk: str = "",
        next_action: str = "",
        rank: int | None = None,
        source_path: str = "",
        evidence_class: str = "repository_canon_extraction",
    ) -> TheoryNode:
        canonical = normalize_label(label)
        key = node_key(canonical)
        existing = self._nodes.get(key)
        sources = tuple(
            sorted(
                {
                    *(existing.source_paths if existing else ()),
                    *([source_path] if source_path else []),
                }
            )
        )
        if existing is None:
            chosen_status = oak_status
        elif oak_status == "unclassified":
            chosen_status = existing.oak_status
        elif _status_score(oak_status) > _status_score(existing.oak_status):
            chosen_status = oak_status
        else:
            chosen_status = existing.oak_status
        chosen_role = role or (existing.role if existing else "")
        chosen_risk = risk or (existing.risk if existing else "")
        chosen_next = next_action or (existing.next_action if existing else "")
        chosen_rank = rank if rank is not None else (existing.rank if existing else None)
        chosen_domain = domain if domain != "cross-domain" else (existing.domain if existing else domain)
        chosen_kind = kind if kind != "theory_system" or existing is None else existing.kind
        node = TheoryNode(
            node_id=stable_id("node", key),
            label=canonical,
            kind=chosen_kind,
            domain=chosen_domain,
            oak_status=chosen_status,
            role=chosen_role,
            risk=chosen_risk,
            next_action=chosen_next,
            rank=chosen_rank,
            utility_score=utility_score(chosen_status, chosen_rank, chosen_next, chosen_role),
            source_paths=sources,
            evidence_class=evidence_class if existing is None else existing.evidence_class,
        )
        self._nodes[key] = node
        return node

    def _add_edge(
        self,
        kind: str,
        labels: Sequence[str],
        *,
        weight: float,
        rationale: str,
        evidence_paths: Iterable[str],
        status: str = "candidate_relation_from_canon",
        edge_seed: str | None = None,
    ) -> None:
        nodes = [self._upsert_node(label) for label in labels]
        node_ids = tuple(node.node_id for node in nodes)
        edge_id = stable_id("hedge", edge_seed or kind, *sorted(node_ids))
        self._edges[edge_id] = KnowledgeHyperedge(
            edge_id=edge_id,
            kind=kind,
            node_ids=node_ids,
            weight=round(float(weight), 3),
            rationale=rationale,
            evidence_paths=tuple(sorted(set(evidence_paths))),
            status=status,
        )

    def ingest_theory_canon(self, payload: Mapping[str, Any], source_path: str) -> None:
        for entry in payload.get("entries", []) or []:
            if not isinstance(entry, Mapping) or not entry.get("name"):
                continue
            node = self._upsert_node(
                str(entry["name"]),
                oak_status=str(entry.get("status") or "unclassified"),
                role=str(entry.get("role") or ""),
                risk=str(entry.get("risk") or ""),
                next_action=str(entry.get("next") or ""),
                source_path=source_path,
                evidence_class="structured_theory_canon",
            )
            if node.risk:
                risk_node = self._upsert_node(
                    f"Risk: {node.risk}",
                    kind="risk",
                    domain="governance",
                    oak_status="review_required",
                    role="Failure boundary extracted from theory canon.",
                    source_path=source_path,
                )
                self._add_edge(
                    "system_has_risk",
                    (node.label, risk_node.label),
                    weight=0.92,
                    rationale="Explicit risk field in structured theory canon.",
                    evidence_paths=(source_path,),
                    status="explicit_structured_relation",
                )
            if node.next_action:
                action_node = self._upsert_node(
                    f"Next: {node.next_action}",
                    kind="next_action",
                    domain="operations",
                    oak_status="proposed",
                    role="Smallest explicit next action extracted from canon.",
                    source_path=source_path,
                )
                self._add_edge(
                    "system_routes_to_next_action",
                    (node.label, action_node.label),
                    weight=0.94,
                    rationale="Explicit next-action field in structured theory canon.",
                    evidence_paths=(source_path,),
                    status="explicit_structured_relation",
                )

    def ingest_master_canon(self, text: str, source_path: str) -> None:
        current_layer: str | None = None
        current_domain = "cross-domain"
        in_candidate_block = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            layer_match = re.match(r"###\s+Layer\s+[A-Z]\s+-\s+(.+)", line)
            if layer_match:
                current_layer = normalize_label(layer_match.group(1))
                current_domain = _LAYER_DOMAIN.get(current_layer.casefold(), "cross-domain")
                self._upsert_node(
                    f"Layer: {current_layer}",
                    kind="layer",
                    domain=current_domain,
                    oak_status="canonical_structure",
                    role="Master Canon layer.",
                    source_path=source_path,
                )
                in_candidate_block = False
                continue
            if line.startswith("Initial candidates:") or line.startswith("Canonical primitives:"):
                in_candidate_block = True
                continue
            if line.startswith("## ") or line.startswith("### "):
                in_candidate_block = False
            if not in_candidate_block or not line.startswith("- ") or current_layer is None:
                continue
            item = line[2:].strip()
            token_match = re.match(r"`([^`]+)`\s*:\s*(.+)", item)
            plain_match = re.match(r"([^:]+):\s*(.+)", item)
            if token_match:
                label, role = token_match.group(1), token_match.group(2)
            elif plain_match:
                label, role = plain_match.group(1), plain_match.group(2)
            else:
                label = item.rstrip(".")
                role = "Candidate or primitive listed in the Master Canon."
            node = self._upsert_node(
                label,
                domain=current_domain,
                oak_status="master_canon_candidate",
                role=role,
                source_path=source_path,
                evidence_class="master_canon_listing",
            )
            self._add_edge(
                "system_belongs_to_layer",
                (node.label, f"Layer: {current_layer}"),
                weight=0.95,
                rationale="Explicit listing under a Master Canon layer.",
                evidence_paths=(source_path,),
                status="explicit_document_structure",
            )

        pipeline_match = re.search(
            r"raw intuition\s*->\s*formal object\s*->\s*equation\s*->\s*proof/test\s*->\s*algorithm\s*->\s*simulation\s*->\s*prototype\s*->\s*measurement\s*->\s*OAK status\s*->\s*canon update",
            text,
            re.IGNORECASE,
        )
        if pipeline_match:
            stages = (
                "Raw intuition",
                "Formal object",
                "Equation",
                "Proof or test",
                "Algorithm",
                "Simulation",
                "Prototype",
                "Measurement",
                "OAK status",
                "Canon update",
            )
            for stage in stages:
                self._upsert_node(
                    stage,
                    kind="workflow_stage",
                    domain="epistemic_pipeline",
                    oak_status="canonical_process",
                    role="Stage in the canonical theory-to-canon pipeline.",
                    source_path=source_path,
                )
            for left, right in zip(stages, stages[1:]):
                self._add_edge(
                    "pipeline_transition",
                    (left, right),
                    weight=0.97,
                    rationale="Ordered transition in the Master Canon operational pipeline.",
                    evidence_paths=(source_path,),
                    status="explicit_pipeline_relation",
                )

    def ingest_system_index(self, text: str, source_path: str) -> None:
        ranked_labels: list[tuple[int, str]] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != 6 or not cells[0].isdigit():
                continue
            rank = int(cells[0])
            label = normalize_label(cells[1])
            repo_path = cells[2].replace("`", "").strip()
            status = cells[3]
            role = cells[4]
            next_action = cells[5]
            node = self._upsert_node(
                label,
                oak_status=status,
                role=role,
                next_action=next_action,
                rank=rank,
                source_path=source_path,
                evidence_class="ranked_master_system_index",
            )
            ranked_labels.append((rank, node.label))
            source_node = self._upsert_node(
                f"Repository path: {repo_path}",
                kind="repository_path",
                domain="provenance",
                oak_status="source_pointer",
                role="Primary repository path from Master System Index.",
                source_path=source_path,
            )
            self._add_edge(
                "system_has_primary_repository_path",
                (node.label, source_node.label),
                weight=0.98,
                rationale="Explicit primary path in Master System Index.",
                evidence_paths=(source_path,),
                status="explicit_structured_relation",
            )

        ranked_labels.sort()
        for (left_rank, left), (right_rank, right) in zip(ranked_labels, ranked_labels[1:]):
            self._add_edge(
                "priority_precedes",
                (left, right),
                weight=round(max(0.55, 0.92 - 0.02 * left_rank), 3),
                rationale=f"Adjacent priority ranks {left_rank} and {right_rank} in Master System Index.",
                evidence_paths=(source_path,),
                status="explicit_priority_order",
            )

    def add_core_relations(self, evidence_paths: Sequence[str]) -> None:
        for seed, kind, labels, weight, rationale in _CORE_RELATIONS:
            self._add_edge(
                kind,
                labels,
                weight=weight,
                rationale=rationale,
                evidence_paths=evidence_paths,
                status="curated_relation_from_canon_cross_reading",
                edge_seed=seed,
            )

    def build(self, *, source_paths: Sequence[str]) -> TheoryHypergraph:
        nodes = sorted(self._nodes.values(), key=lambda node: (-node.utility_score, node.label.casefold()))
        edges = sorted(self._edges.values(), key=lambda edge: (edge.kind, edge.edge_id))
        graph = TheoryHypergraph(
            nodes=nodes,
            hyperedges=edges,
            manifest={
                "schema": "omega_wiki_t.theory_hypergraph.v0.2",
                "source_paths": list(source_paths),
                "node_count": len(nodes),
                "hyperedge_count": len(edges),
                "oak_status": "REPOSITORY_CANON_ABSORBED_NOT_SCIENTIFICALLY_CERTIFIED",
                "utility_score_boundary": "Transparent navigation heuristic from OAK status, rank, next action, and actionability; not truth probability.",
                "relation_boundary": "Explicit document relations and curated cross-reading links remain candidate knowledge relations until reviewed.",
            },
        )
        issues = graph.validate()
        if issues:
            raise ValueError(f"Invalid theory hypergraph: {issues}")
        return graph

    @classmethod
    def from_files(
        cls,
        *,
        theory_canon_json: str | Path,
        master_canon: str | Path,
        system_index: str | Path,
    ) -> TheoryHypergraph:
        canon_path = Path(theory_canon_json)
        master_path = Path(master_canon)
        index_path = Path(system_index)
        builder = cls()
        builder.ingest_theory_canon(json.loads(canon_path.read_text(encoding="utf-8")), str(canon_path))
        builder.ingest_master_canon(master_path.read_text(encoding="utf-8"), str(master_path))
        builder.ingest_system_index(index_path.read_text(encoding="utf-8"), str(index_path))
        builder.add_core_relations((str(canon_path), str(master_path), str(index_path)))
        return builder.build(source_paths=(str(canon_path), str(master_path), str(index_path)))

    @staticmethod
    def write(graph: TheoryHypergraph, output_dir: str | Path) -> Path:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "manifest.json").write_text(
            json.dumps(graph.manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (out / "knowledge-hypergraph.json").write_text(
            json.dumps(graph.to_json_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (out / "theory-nodes.jsonl").write_text(
            "".join(json.dumps(asdict(node), ensure_ascii=False) + "\n" for node in graph.nodes),
            encoding="utf-8",
        )
        (out / "knowledge-hyperedges.jsonl").write_text(
            "".join(json.dumps(asdict(edge), ensure_ascii=False) + "\n" for edge in graph.hyperedges),
            encoding="utf-8",
        )
        (out / "knowledge-hypergraph.graphml").write_text(render_graphml(graph), encoding="utf-8")
        (out / "useful-knowledge.md").write_text(render_useful_knowledge(graph), encoding="utf-8")
        return out


def render_graphml(graph: TheoryHypergraph) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
        '  <key id="utility" for="node" attr.name="utility" attr.type="double"/>',
        '  <key id="edge_kind" for="edge" attr.name="kind" attr.type="string"/>',
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '  <graph edgedefault="undirected">',
    ]
    for node in graph.nodes:
        lines.append(
            f"    <node id={quoteattr(node.node_id)}><data key=\"kind\">{escape(node.kind)}</data>"
            f"<data key=\"label\">{escape(node.label)}</data><data key=\"utility\">{node.utility_score}</data></node>"
        )
    for hyperedge in graph.hyperedges:
        hyper_node = f"hyperedge:{hyperedge.edge_id}"
        lines.append(
            f"    <node id={quoteattr(hyper_node)}><data key=\"kind\">hyperedge</data>"
            f"<data key=\"label\">{escape(hyperedge.kind)}</data><data key=\"utility\">{hyperedge.weight}</data></node>"
        )
        for index, node_id in enumerate(hyperedge.node_ids):
            edge_id = f"{hyperedge.edge_id}:{index}"
            lines.append(
                f"    <edge id={quoteattr(edge_id)} source={quoteattr(hyper_node)} target={quoteattr(node_id)}>"
                f"<data key=\"edge_kind\">participant</data><data key=\"weight\">{hyperedge.weight}</data></edge>"
            )
    lines.extend(("  </graph>", "</graphml>"))
    return "\n".join(lines) + "\n"


def render_useful_knowledge(graph: TheoryHypergraph) -> str:
    systems = [node for node in graph.nodes if node.kind == "theory_system"]
    top = systems[:16]
    relation_kinds: dict[str, int] = {}
    for edge in graph.hyperedges:
        relation_kinds[edge.kind] = relation_kinds.get(edge.kind, 0) + 1
    lines = [
        "# Ω-WIKI-T∞ — Hypergraphe des connaissances utiles",
        "",
        f"- Nœuds: **{len(graph.nodes)}**",
        f"- Hyperarêtes: **{len(graph.hyperedges)}**",
        f"- Sources canoniques: {', '.join(f'`{path}`' for path in graph.manifest['source_paths'])}",
        "- Statut OAK: **absorption structurée du dépôt, pas certification scientifique**",
        "",
        "## Colonne vertébrale utile",
        "",
        "```text",
        "TFUGA → HGFM → CVCD",
        "          ↘ OAK ↔ DCT-Ω / DCT++ ↔ AI-7",
        "             ↕",
        "      Bayes-Tristan + FailureSynth",
        "             ↓",
        "AUTO² / Ω-LIN-T / FFWT-HAC-CVCD / DeepTech Forge",
        "             ↓",
        "preuve locale → prototype → publication/IP/revenu avec validation humaine",
        "```",
        "",
        "## Noyaux classés par utilité opérationnelle",
        "",
        "Le score ci-dessous sert uniquement à naviguer et prioriser. Il combine statut OAK déclaré, rang du Master System Index, présence d’une prochaine action et caractère testable/exécutable.",
        "",
        "| Priorité | Système | Score | Statut | Domaine | Prochaine action |",
        "|---:|---|---:|---|---|---|",
    ]
    for index, node in enumerate(top, start=1):
        next_action = node.next_action.replace("|", "/") or "à définir"
        lines.append(
            f"| {index} | {node.label} | {node.utility_score:.3f} | {node.oak_status} | {node.domain} | {next_action} |"
        )
    lines.extend(("", "## Types de relations", ""))
    for kind, count in sorted(relation_kinds.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{kind}`: {count}")
    lines.extend(
        (
            "",
            "## Routes immédiatement utiles",
            "",
            "1. **Rigueur générale** — faire passer chaque théorie par `DCT-Ω / DCT++ → OAK → test/résidu → statut`.",
            "2. **Prototype scientifique** — prioriser `Ω-LIN-T` et `FFWT-HAC-CVCD`, car ils possèdent déjà des chemins de benchmark explicites.",
            "3. **Compagnie et valeur** — utiliser `Ω-DeepTech Intelligence Forge → Company Revenue IP Publication OS`, sans confondre signal, brevet, vente ou certification.",
            "4. **Mémoire anti-erreur** — relier chaque échec à `FailureSynth → OAK` afin qu’un résidu devienne une règle réutilisable.",
            "5. **Recherche externe** — connecter ensuite chaque nœud à WikiForge-T multilingue pour ajouter sources Wikipédia, Wikidata, DOI/ISBN/PMID et contradictions documentaires.",
            "",
            "## Limites OAK",
            "",
            "- Le graphe décrit le corpus et ses routes de travail; il ne prouve aucune conjecture physique.",
            "- Les hyperarêtes issues d’une lecture croisée sont marquées comme relations candidates.",
            "- Le score d’utilité n’est ni une probabilité de vérité ni une valeur économique.",
            "- Toute publication, brevet, décision sensible ou revendication scientifique demeure sous validation humaine.",
            "",
        )
    )
    return "\n".join(lines)
