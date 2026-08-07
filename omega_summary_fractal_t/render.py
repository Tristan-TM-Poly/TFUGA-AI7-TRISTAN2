from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .models import SummaryBundle, SummaryNode

AUDIENCE_HINTS = {
    "tristan": "Architecture, preuves, dette de cristallisation et prochaines actions.",
    "developer": "Code, fichiers, tests, contrats et points d'intégration.",
    "scientist": "Hypothèses observables, preuves, limites et reproductibilité.",
    "investor": "État de réalisation et preuves techniques; aucune traction n'est inférée.",
    "client": "Capacités observables; aucun bénéfice non démontré n'est inventé.",
    "ip": "Provenance structurelle; le statut brevet/secret/publication exige IPGate.",
    "contributor": "Où se trouve le code, ce qui est testé et les lacunes prioritaires.",
    "oak": "Séparation stricte entre documenté, implémenté, testé et validé.",
}


def _chronological_systems(nodes: list[SummaryNode]) -> list[SummaryNode]:
    return sorted(
        (node for node in nodes if node.kind == "system"),
        key=lambda node: (
            not bool(node.metrics.get("first_seen")),
            str(node.metrics.get("first_seen", "")),
            int(node.metrics.get("chronology_rank", 10**9)),
            node.path,
        ),
    )


def _system_table(nodes: list[SummaryNode]) -> str:
    systems = _chronological_systems(nodes)
    if not systems:
        return "_Aucun système visible à cette profondeur ou pour ce focus._"
    lines = [
        "| # | Première trace Git | Système | Statut | Code | Tests | CI | Docs | Schéma | Résumé |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for node in systems:
        metrics = node.metrics
        summary = node.one_line.replace("|", "\\|")
        first_seen = str(metrics.get("first_seen", "")) or "—"
        rank = metrics.get("chronology_rank", "—")
        lines.append(
            f"| {rank} | {first_seen} | `{node.path}` | {node.status} | "
            f"{metrics.get('code_files', 0)} | {metrics.get('tests', 0)} | "
            f"{metrics.get('workflows', 0)} | {metrics.get('documents', 0)} | "
            f"{metrics.get('schemas', 0)} | {summary} |"
        )
    return "\n".join(lines)


def _relation_summary(bundle: SummaryBundle) -> str:
    counts = Counter(edge.relation for edge in bundle.edges if edge.relation != "CONTAINS")
    if not counts:
        return "_Aucune relation transversale visible à cette profondeur._"
    return "\n".join(f"- `{relation}` : **{counts[relation]}**" for relation in sorted(counts))


def render_markdown(bundle: SummaryBundle) -> str:
    health = bundle.health
    oak = health.get("oak", {})
    lines = [
        f"# Ω-SUMMARY-FRACTAL — {bundle.root}",
        "",
        f"- **Profondeur :** D{bundle.depth}",
        f"- **Audience :** `{bundle.audience}` — {AUDIENCE_HINTS[bundle.audience]}",
        f"- **Focus :** `{bundle.focus or 'corpus local'}`",
        f"- **Empreinte :** `{bundle.cache_fingerprint}`",
        f"- **Généré :** {bundle.generated_at}",
        "",
        "## Chronologie structurelle",
        "",
        _system_table(bundle.nodes),
        "",
        "La date `first_seen` est une provenance Git observée. Une histoire Git peu profonde ou réécrite peut rendre cette chronologie partielle; aucune date manquante n'est inventée.",
        "",
        "## Relations de preuve et dépendance",
        "",
        _relation_summary(bundle),
        "",
        "## Santé du corpus",
        "",
        f"- systèmes détectés : **{health.get('systems', 0)}**",
        f"- ratio implémenté : **{health.get('implemented_ratio', 0):.1%}**",
        f"- ratio testé : **{health.get('tested_ratio', 0):.1%}**",
        f"- ratio documenté : **{health.get('documented_ratio', 0):.1%}**",
        f"- ratio avec schéma : **{health.get('schema_backed_ratio', 0):.1%}**",
        "",
        "## OAK",
        "",
        f"- **Vérité :** {oak.get('truth', '')}",
        f"- **Produit :** {oak.get('product', '')}",
        f"- **IP :** {oak.get('ip', '')}",
        f"- **Revenu :** {oak.get('revenue', '')}",
        f"- **Risque :** {oak.get('risk', '')}",
        "",
    ]
    if bundle.depth >= 3:
        lines += ["## Lacunes prioritaires", ""]
        lines += [
            f"- P{gap['priority']} `{gap['system']}` — **{gap['kind']}**: {gap['action']}"
            for gap in bundle.gaps[:100]
        ] or ["_Aucune lacune structurelle détectée par les règles actuelles._"]
        lines.append("")
    if bundle.depth >= 4:
        lines += ["## Candidats de déduplication", ""]
        lines += [
            f"- `{item['left']}` ↔ `{item['right']}` — similarité {item['similarity']:.2f}; revue humaine requise."
            for item in bundle.duplicate_candidates[:50]
        ] or ["_Aucun quasi-doublon au-dessus du seuil heuristique._"]
        lines.append("")
    if bundle.depth >= 5:
        lines += ["## Artefacts observés", ""]
        by_kind: dict[str, list[SummaryNode]] = {}
        for node in bundle.nodes:
            if node.kind not in {"repository", "system"}:
                by_kind.setdefault(node.kind, []).append(node)
        for kind in sorted(by_kind):
            lines.append(f"### {kind}")
            lines += [f"- `{node.path}` — {node.one_line}" for node in by_kind[kind][:200]]
            lines.append("")
    lines += [
        "## Limite épistémique",
        "",
        "Ce document résume des artefacts Git observables. La présence de code, de tests, de CI, de schémas, de grands espaces logiques ou d'objets générés ne constitue pas à elle seule une validation scientifique, commerciale, juridique ou de sécurité.",
        "",
    ]
    return "\n".join(lines)


def write_bundle(bundle: SummaryBundle, output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"summary_d{bundle.depth}_{bundle.audience}"
    json_path = out / f"{stem}.json"
    markdown_path = out / f"{stem}.md"
    json_path.write_text(
        json.dumps(bundle.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(bundle), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def write_operational_views(bundle: SummaryBundle, output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = out / "SUMMARY.md"
    summary.write_text(render_markdown(bundle), encoding="utf-8")
    status = out / "STATUS.md"
    status.write_text(
        "# STATUS\n\n" + _system_table(bundle.nodes) + "\n\nStatuses are inferred only from observable repository artifacts and linked validation evidence.\n",
        encoding="utf-8",
    )
    oak = out / "OAK_REPORT.md"
    oak.write_text(
        "# OAK REPORT\n\n"
        + f"Fingerprint: `{bundle.cache_fingerprint}`\n\n"
        + "## Boundary\n\nStructural evidence only. No scientific validity, novelty, patentability, safety, market traction, or causal truth is inferred. Generated volume and logical address-space size are not evidence of discovery.\n\n"
        + "## Dashboard\n\n"
        + f"```json\n{json.dumps(bundle.health, indent=2, ensure_ascii=False, sort_keys=True)}\n```\n",
        encoding="utf-8",
    )
    actions = out / "NEXT_ACTIONS.md"
    action_lines = ["# NEXT ACTIONS", ""] + [
        f"- [ ] P{gap['priority']} `{gap['system']}` — {gap['action']}"
        for gap in bundle.gaps[:100]
    ]
    action_lines += [] if bundle.gaps else [
        "- [ ] Run deeper semantic/OAK review; structural checks found no immediate gaps."
    ]
    actions.write_text("\n".join(action_lines) + "\n", encoding="utf-8")
    index = out / "SUMMARY_INDEX.json"
    index.write_text(
        json.dumps(
            {
                "schema_version": bundle.schema_version,
                "fingerprint": bundle.cache_fingerprint,
                "depth": bundle.depth,
                "audience": bundle.audience,
                "focus": bundle.focus,
                "artifacts": ["SUMMARY.md", "STATUS.md", "OAK_REPORT.md", "NEXT_ACTIONS.md"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "status": status, "oak": oak, "actions": actions, "index": index}
