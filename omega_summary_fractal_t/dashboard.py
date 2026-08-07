from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .index import longitudinal_metrics
from .query import query_payload


def _load_payload(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _proof_debt_from_result(item: Mapping[str, Any]) -> int:
    metrics = item.get("metrics", {})
    implemented = bool(metrics.get("implemented") or int(metrics.get("code_files", 0) or 0))
    missing = 0
    if not (metrics.get("documented") or int(metrics.get("documents", 0) or 0)):
        missing += 1
    if not implemented:
        missing += 1
    if implemented and not (metrics.get("tested") or int(metrics.get("tests", 0) or 0)):
        missing += 1
    if implemented and not int(metrics.get("workflows", 0) or 0):
        missing += 1
    if implemented and not (metrics.get("schema_backed") or int(metrics.get("schemas", 0) or 0)):
        missing += 1
    return missing


def build_dashboard(
    summary: str | Path | Mapping[str, Any],
    *,
    index: str | Path | Mapping[str, Any] | None = None,
    top_n: int = 20,
) -> dict[str, Any]:
    payload = _load_payload(summary)
    query = query_payload(payload, kind="system", limit=1_000_000)
    systems = list(query.get("results", []))
    status_counts = Counter(str(item.get("status", "observed")) for item in systems)
    repository_counts = Counter(str(item.get("repository", "")) for item in systems)

    for item in systems:
        item["structural_proof_debt"] = _proof_debt_from_result(item)

    crystallized = sorted(
        systems,
        key=lambda item: (-float(item.get("structural_crystallization") or 0.0), int(item.get("structural_proof_debt", 0)), item.get("path", "")),
    )[:top_n]
    debt = sorted(
        systems,
        key=lambda item: (-int(item.get("structural_proof_debt", 0)), float(item.get("structural_crystallization") or 0.0), item.get("path", "")),
    )[:top_n]
    needs_tests = [
        item for item in systems
        if bool(item.get("metrics", {}).get("implemented") or int(item.get("metrics", {}).get("code_files", 0) or 0))
        and not bool(item.get("metrics", {}).get("tested") or int(item.get("metrics", {}).get("tests", 0) or 0))
    ]
    needs_ci = [
        item for item in systems
        if bool(item.get("metrics", {}).get("implemented") or int(item.get("metrics", {}).get("code_files", 0) or 0))
        and not int(item.get("metrics", {}).get("workflows", 0) or 0)
    ]
    needs_schema = [
        item for item in systems
        if bool(item.get("metrics", {}).get("implemented") or int(item.get("metrics", {}).get("code_files", 0) or 0))
        and not bool(item.get("metrics", {}).get("schema_backed") or int(item.get("metrics", {}).get("schemas", 0) or 0))
    ]

    relations = Counter()
    if isinstance(payload.get("edges"), list):
        relations.update(str(edge.get("relation", "")) for edge in payload.get("edges", []) if edge.get("relation"))
    elif isinstance(payload.get("cross_repo_links"), list):
        relations.update(str(edge.get("relation", "")) for edge in payload.get("cross_repo_links", []) if edge.get("relation"))

    longitudinal: dict[str, Any] | None = None
    if index is not None:
        index_payload = _load_payload(index)
        longitudinal = longitudinal_metrics(index_payload)

    mean_crystallization = (
        round(sum(float(item.get("structural_crystallization") or 0.0) for item in systems) / len(systems), 4)
        if systems else 0.0
    )
    mean_debt = (
        round(sum(int(item.get("structural_proof_debt", 0)) for item in systems) / len(systems), 4)
        if systems else 0.0
    )

    return {
        "schema_version": "1.0.0",
        "systems": len(systems),
        "repositories": len(repository_counts),
        "status_counts": dict(sorted(status_counts.items())),
        "repository_counts": dict(sorted(repository_counts.items())),
        "relation_counts": dict(sorted(relations.items())),
        "mean_structural_crystallization": mean_crystallization,
        "mean_structural_proof_debt": mean_debt,
        "attention": {
            "implemented_without_tests": len(needs_tests),
            "implemented_without_linked_ci": len(needs_ci),
            "implemented_without_machine_contract": len(needs_schema),
        },
        "top_crystallized": crystallized,
        "top_structural_debt": debt,
        "longitudinal": longitudinal,
        "boundary": "dashboard scores summarize observable repository crystallization only; they are not rankings of scientific truth, originality, safety, legal validity, IP strength, product-market fit or economic value",
    }


def _short_rows(items: list[Mapping[str, Any]], limit: int = 15) -> list[str]:
    rows = []
    for item in items[:limit]:
        rows.append(
            f"| `{item.get('repository', '')}` | `{item.get('path', '')}` | {item.get('status', '')} | "
            f"{float(item.get('structural_crystallization') or 0.0):.2f} | {int(item.get('structural_proof_debt', 0))} |"
        )
    return rows


def render_dashboard_markdown(report: Mapping[str, Any]) -> str:
    attention = report.get("attention", {})
    lines = [
        "# Ω-SUMMARY CORPUS DASHBOARD",
        "",
        f"- systèmes : **{report.get('systems', 0)}**",
        f"- dépôts : **{report.get('repositories', 0)}**",
        f"- cristallisation structurelle moyenne : **{float(report.get('mean_structural_crystallization', 0.0)):.3f}**",
        f"- dette structurelle moyenne : **{float(report.get('mean_structural_proof_debt', 0.0)):.3f}**",
        f"- implémentés sans tests liés : **{attention.get('implemented_without_tests', 0)}**",
        f"- implémentés sans CI liée : **{attention.get('implemented_without_linked_ci', 0)}**",
        f"- implémentés sans contrat machine : **{attention.get('implemented_without_machine_contract', 0)}**",
        "",
        "## Statuts",
        "",
    ]
    for status, count in report.get("status_counts", {}).items():
        lines.append(f"- `{status}` : **{count}**")
    lines += ["", "## Relations observées", ""]
    for relation, count in report.get("relation_counts", {}).items():
        lines.append(f"- `{relation}` : **{count}**")
    if not report.get("relation_counts"):
        lines.append("_Aucune relation disponible dans cette projection._")

    lines += [
        "",
        "## Systèmes les plus cristallisés structurellement",
        "",
        "| Repository | Système | Statut | C_struct | Dette |",
        "|---|---|---|---:|---:|",
    ]
    lines += _short_rows(list(report.get("top_crystallized", []))) or ["| — | — | — | — | — |"]
    lines += [
        "",
        "## Dette structurelle la plus élevée",
        "",
        "| Repository | Système | Statut | C_struct | Dette |",
        "|---|---|---|---:|---:|",
    ]
    lines += _short_rows(list(report.get("top_structural_debt", []))) or ["| — | — | — | — | — |"]

    longitudinal = report.get("longitudinal")
    if longitudinal:
        improving = sorted(
            longitudinal.get("systems", []),
            key=lambda item: (-float(item.get("crystallization_delta", 0.0)), int(item.get("proof_debt_delta", 0)), item.get("entity", "")),
        )[:15]
        lines += [
            "",
            "## Évolution structurelle",
            "",
            f"- runs observés : **{longitudinal.get('run_count', 0)}**",
            f"- chaîne valide : **{bool(longitudinal.get('valid_hash_chain'))}**",
            "",
            "| Système | Δ cristallisation | Δ dette |",
            "|---|---:|---:|",
        ]
        for item in improving:
            lines.append(
                f"| `{item.get('entity', '')}` | {float(item.get('crystallization_delta', 0.0)):+.3f} | {int(item.get('proof_debt_delta', 0)):+d} |"
            )

    lines += ["", "## OAK boundary", "", str(report.get("boundary", "")), ""]
    return "\n".join(lines)


def write_dashboard(
    summary: str | Path | Mapping[str, Any],
    output_dir: str | Path,
    *,
    index: str | Path | Mapping[str, Any] | None = None,
    top_n: int = 20,
) -> dict[str, Path]:
    report = build_dashboard(summary, index=index, top_n=top_n)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "CORPUS_DASHBOARD.json"
    markdown_path = out / "CORPUS_DASHBOARD.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_dashboard_markdown(report), encoding="utf-8")
    return {"dashboard_json": json_path, "dashboard_markdown": markdown_path}
