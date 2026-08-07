from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from .models import SummaryBundle, SummaryNode

TOKEN_RE = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)
GENERIC = {"omega", "tfuga", "sage", "ecc", "ait", "tristan", "system", "systems", "the", "and", "for"}


def _tokens(node: SummaryNode) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(
            f"{node.path} {node.title} {node.one_line}".casefold().replace("-", "_")
        )
        if token not in GENERIC and token != "t"
    }


def build_system_lineage(bundle: SummaryBundle) -> dict[str, Any]:
    """Build a deterministic, evidence-bounded lineage projection.

    The output is intentionally structural: Git chronology, repository status and
    observed graph relations. It does not claim scientific descent, authorship,
    novelty, IP ownership or causal influence.
    """

    systems = sorted(
        (node for node in bundle.nodes if node.kind == "system"),
        key=lambda node: (
            not bool(node.metrics.get("first_seen")),
            str(node.metrics.get("first_seen", "")),
            int(node.metrics.get("chronology_rank", 10**9)),
            node.path,
        ),
    )
    by_id = {node.id: node for node in bundle.nodes}
    outgoing: dict[str, list[dict[str, str]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, str]]] = defaultdict(list)
    for edge in bundle.edges:
        if edge.relation == "CONTAINS":
            continue
        target = by_id.get(edge.target)
        source = by_id.get(edge.source)
        outgoing[edge.source].append(
            {
                "relation": edge.relation,
                "target": target.path if target else edge.target,
                "target_kind": target.kind if target else "unknown",
            }
        )
        incoming[edge.target].append(
            {
                "relation": edge.relation,
                "source": source.path if source else edge.source,
                "source_kind": source.kind if source else "unknown",
            }
        )

    records = []
    for node in systems:
        records.append(
            {
                "chronology_rank": node.metrics.get("chronology_rank"),
                "first_seen": node.metrics.get("first_seen", ""),
                "chronology_source": node.metrics.get("chronology_source", "unavailable"),
                "system": node.path,
                "title": node.title,
                "status": node.status,
                "metrics": {
                    key: node.metrics.get(key, 0)
                    for key in (
                        "code_files",
                        "tests",
                        "workflows",
                        "documents",
                        "schemas",
                    )
                },
                "outgoing_relations": sorted(
                    outgoing.get(node.id, []),
                    key=lambda item: (item["relation"], item["target"]),
                ),
                "incoming_relations": sorted(
                    incoming.get(node.id, []),
                    key=lambda item: (item["relation"], item["source"]),
                ),
            }
        )
    return {
        "schema_version": "1.0.0",
        "root": bundle.root,
        "fingerprint": bundle.cache_fingerprint,
        "boundary": "structural Git lineage only; not scientific genealogy, novelty, ownership or causality",
        "systems": records,
    }


def proof_debt(bundle: SummaryBundle) -> list[dict[str, Any]]:
    """Return a conservative structural proof-debt ledger per system."""

    debt = []
    for node in sorted((n for n in bundle.nodes if n.kind == "system"), key=lambda n: n.path):
        metrics = node.metrics
        missing = []
        if not metrics.get("documented"):
            missing.append("documentation")
        if not metrics.get("implemented"):
            missing.append("implementation")
        if metrics.get("implemented") and not metrics.get("tested"):
            missing.append("focused_tests")
        if metrics.get("implemented") and not metrics.get("schema_backed"):
            missing.append("machine_contract")
        if metrics.get("implemented") and not metrics.get("workflows"):
            missing.append("linked_ci")
        # External validation is deliberately never inferred from repository structure.
        missing.append("external_validation_not_inferred")
        score = sum(item != "external_validation_not_inferred" for item in missing)
        debt.append(
            {
                "system": node.path,
                "status": node.status,
                "structural_debt_score": score,
                "missing": missing,
                "boundary": "external scientific/commercial/legal validation must be established separately",
            }
        )
    return sorted(
        debt,
        key=lambda item: (-int(item["structural_debt_score"]), str(item["system"])),
    )


def _dependency_map(bundle: SummaryBundle) -> dict[str, set[str]]:
    dependencies: dict[str, set[str]] = defaultdict(set)
    for edge in bundle.edges:
        if edge.relation == "DEPENDS_ON":
            dependencies[edge.source].add(edge.target)
    return dependencies


def _validation_signature(node: SummaryNode) -> set[str]:
    metrics = node.metrics
    signature = set()
    if metrics.get("implemented"):
        signature.add("code")
    if metrics.get("tested"):
        signature.add("tests")
    if metrics.get("workflows"):
        signature.add("ci")
    if metrics.get("schema_backed"):
        signature.add("schema")
    if metrics.get("documented"):
        signature.add("docs")
    return signature


def convergence_candidates(bundle: SummaryBundle, threshold: float = 0.45) -> list[dict[str, Any]]:
    """Find review-only structural convergence candidates.

    Multiple weak evidence channels are retained separately. The score is only a
    routing heuristic for possible shared kernels, never identity or an automatic
    merge decision.
    """

    systems = sorted((node for node in bundle.nodes if node.kind == "system"), key=lambda n: n.path)
    dependencies = _dependency_map(bundle)
    direct_pairs = {
        tuple(sorted((edge.source, edge.target)))
        for edge in bundle.edges
        if edge.relation == "DEPENDS_ON"
    }
    out = []
    for index, left in enumerate(systems):
        left_tokens = _tokens(left)
        left_validation = _validation_signature(left)
        for right in systems[index + 1 :]:
            right_tokens = _tokens(right)
            union = left_tokens | right_tokens
            if not union:
                continue
            lexical = len(left_tokens & right_tokens) / len(union)
            pair = tuple(sorted((left.id, right.id)))
            direct_dependency = pair in direct_pairs
            shared_dependencies = dependencies.get(left.id, set()) & dependencies.get(right.id, set())
            validation_union = left_validation | _validation_signature(right)
            validation_overlap = (
                len(left_validation & _validation_signature(right)) / len(validation_union)
                if validation_union
                else 0.0
            )

            score = lexical
            evidence = []
            if lexical:
                evidence.append(f"lexical_jaccard={lexical:.4f}")
            if direct_dependency:
                score += 0.15
                evidence.append("direct_dependency")
            if shared_dependencies:
                score += min(0.15, 0.05 * len(shared_dependencies))
                evidence.append(f"shared_dependencies={len(shared_dependencies)}")
            if validation_overlap >= 0.8 and left_validation and _validation_signature(right):
                score += 0.05
                evidence.append(f"validation_profile_overlap={validation_overlap:.4f}")
            score = min(1.0, score)
            if score < threshold:
                continue
            out.append(
                {
                    "left": left.path,
                    "right": right.path,
                    "left_id": left.id,
                    "right_id": right.id,
                    "score": round(score, 4),
                    "evidence": evidence,
                    "evidence_channels": len(evidence),
                    "classification": "shared-kernel-candidate",
                    "status": "review_required",
                    "automatic_merge": False,
                }
            )
    return sorted(out, key=lambda item: (-float(item["score"]), item["left"], item["right"]))


def superkernel_candidates(
    bundle: SummaryBundle,
    *,
    pair_threshold: float = 0.45,
    minimum_evidence_channels: int = 2,
) -> list[dict[str, Any]]:
    """Cluster multi-evidence convergence pairs into review-only components."""

    pairs = [
        item
        for item in convergence_candidates(bundle, threshold=pair_threshold)
        if int(item.get("evidence_channels", 0)) >= minimum_evidence_channels
    ]
    adjacency: dict[str, set[str]] = defaultdict(set)
    pair_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in pairs:
        left = str(item["left"])
        right = str(item["right"])
        adjacency[left].add(right)
        adjacency[right].add(left)
        pair_lookup[tuple(sorted((left, right)))] = item

    visited: set[str] = set()
    clusters = []
    for seed in sorted(adjacency):
        if seed in visited:
            continue
        stack = [seed]
        members: set[str] = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            members.add(current)
            stack.extend(sorted(adjacency.get(current, set()) - visited))
        if len(members) < 2:
            continue
        member_list = sorted(members)
        supporting_pairs = []
        evidence_types: set[str] = set()
        for i, left in enumerate(member_list):
            for right in member_list[i + 1 :]:
                item = pair_lookup.get(tuple(sorted((left, right))))
                if not item:
                    continue
                supporting_pairs.append(
                    {
                        "left": left,
                        "right": right,
                        "score": item["score"],
                        "evidence": item["evidence"],
                    }
                )
                for evidence in item["evidence"]:
                    evidence_types.add(str(evidence).split("=", 1)[0])
        clusters.append(
            {
                "cluster_id": "kernel-candidate-pending",
                "members": member_list,
                "member_count": len(member_list),
                "supporting_pairs": supporting_pairs,
                "evidence_types": sorted(evidence_types),
                "classification": "multi-evidence-superkernel-candidate",
                "status": "review_required",
                "automatic_merge": False,
                "boundary": "structural clustering only; no identity, redundancy, novelty or deletion inference",
            }
        )

    clusters.sort(key=lambda item: (-int(item["member_count"]), item["members"]))
    for ordinal, cluster in enumerate(clusters, start=1):
        cluster["cluster_id"] = f"kernel-candidate-{ordinal:03d}"
    return clusters


def render_evolution(bundle: SummaryBundle) -> str:
    lineage = build_system_lineage(bundle)
    lines = [
        "# EVOLUTION",
        "",
        "Chronologie Git structurale des systèmes observés. Les dates manquantes restent manquantes; aucune histoire scientifique n'est inventée.",
        "",
        "| # | Première trace Git | Système | Statut | Code | Tests | CI | Schémas |",
        "|---:|---|---|---|---:|---:|---:|---:|",
    ]
    for item in lineage["systems"]:
        metrics = item["metrics"]
        lines.append(
            f"| {item['chronology_rank']} | {item['first_seen'] or '—'} | `{item['system']}` | "
            f"{item['status']} | {metrics['code_files']} | {metrics['tests']} | "
            f"{metrics['workflows']} | {metrics['schemas']} |"
        )
    lines += [
        "",
        "## OAK boundary",
        "",
        "Cette chronologie mesure l'apparition d'artefacts dans Git. Elle ne prouve ni date d'invention, ni nouveauté scientifique, ni priorité IP, ni causalité entre systèmes.",
        "",
    ]
    return "\n".join(lines)


def render_proof_debt(bundle: SummaryBundle) -> str:
    rows = proof_debt(bundle)
    lines = [
        "# PROOF DEBT",
        "",
        "Dette structurelle de preuve/cristallisation. La validation externe est toujours séparée et n'est jamais déduite du code ou de la CI.",
        "",
        "| Système | Statut | Dette structurelle | Manques |",
        "|---|---|---:|---|",
    ]
    for item in rows:
        missing = ", ".join(item["missing"])
        lines.append(
            f"| `{item['system']}` | {item['status']} | {item['structural_debt_score']} | {missing} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_convergence_candidates(bundle: SummaryBundle) -> str:
    candidates = convergence_candidates(bundle)
    clusters = superkernel_candidates(bundle)
    lines = [
        "# CONVERGENCE CANDIDATES",
        "",
        "Candidats `review_required` pour factoriser des primitives ou super-kernels. **Aucune fusion automatique.** Similarité et dépendance ne prouvent ni identité ni redondance.",
        "",
        "## Paires",
        "",
    ]
    if not candidates:
        lines += ["_Aucun candidat au seuil actuel._", ""]
    else:
        lines += [
            "| Gauche | Droite | Score | Canaux | Preuves structurelles |",
            "|---|---|---:|---:|---|",
        ]
        for item in candidates[:200]:
            lines.append(
                f"| `{item['left']}` | `{item['right']}` | {item['score']:.3f} | {item['evidence_channels']} | {', '.join(item['evidence'])} |"
            )
        lines.append("")

    lines += ["## Super-kernels multi-preuves", ""]
    if not clusters:
        lines += ["_Aucun cluster ne satisfait encore le minimum multi-preuves._", ""]
    else:
        for cluster in clusters[:100]:
            lines.append(
                f"### {cluster['cluster_id']} — {cluster['member_count']} systèmes — review_required"
            )
            lines.append("")
            lines.append("- membres : " + ", ".join(f"`{member}`" for member in cluster["members"]))
            lines.append("- types de preuve : " + ", ".join(cluster["evidence_types"]))
            lines.append("- `automatic_merge=false`")
            lines.append("")
    lines += [
        "## OAK boundary",
        "",
        "Un cluster est un candidat de factorisation architecturale. Il ne prouve ni identité sémantique, ni redondance, ni priorité, ni nouveauté, et n'autorise aucune suppression ou fusion automatique.",
        "",
    ]
    return "\n".join(lines)
