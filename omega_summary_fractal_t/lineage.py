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


def convergence_candidates(bundle: SummaryBundle, threshold: float = 0.45) -> list[dict[str, Any]]:
    """Find review-only structural convergence candidates.

    This is deliberately weaker than identity/deduplication. It is a routing aid
    for possible shared kernels, not an automatic merge proposal.
    """

    systems = sorted((node for node in bundle.nodes if node.kind == "system"), key=lambda n: n.path)
    dependency_pairs = {
        tuple(sorted((edge.source, edge.target)))
        for edge in bundle.edges
        if edge.relation == "DEPENDS_ON"
    }
    out = []
    for index, left in enumerate(systems):
        left_tokens = _tokens(left)
        for right in systems[index + 1 :]:
            right_tokens = _tokens(right)
            union = left_tokens | right_tokens
            if not union:
                continue
            lexical = len(left_tokens & right_tokens) / len(union)
            pair = tuple(sorted((left.id, right.id)))
            dependency_bonus = 0.15 if pair in dependency_pairs else 0.0
            score = min(1.0, lexical + dependency_bonus)
            if score < threshold:
                continue
            evidence = []
            if lexical:
                evidence.append(f"lexical_jaccard={lexical:.4f}")
            if dependency_bonus:
                evidence.append("direct_dependency")
            out.append(
                {
                    "left": left.path,
                    "right": right.path,
                    "score": round(score, 4),
                    "evidence": evidence,
                    "classification": "shared-kernel-candidate",
                    "status": "review_required",
                    "automatic_merge": False,
                }
            )
    return sorted(out, key=lambda item: (-float(item["score"]), item["left"], item["right"]))


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
    lines = [
        "# CONVERGENCE CANDIDATES",
        "",
        "Candidats `review_required` pour factoriser des primitives ou super-kernels. **Aucune fusion automatique.** Similarité et dépendance ne prouvent ni identité ni redondance.",
        "",
    ]
    if not candidates:
        lines += ["_Aucun candidat au seuil actuel._", ""]
        return "\n".join(lines)
    lines += [
        "| Gauche | Droite | Score | Preuves structurelles |",
        "|---|---|---:|---|",
    ]
    for item in candidates[:200]:
        lines.append(
            f"| `{item['left']}` | `{item['right']}` | {item['score']:.3f} | {', '.join(item['evidence'])} |"
        )
    lines.append("")
    return "\n".join(lines)
