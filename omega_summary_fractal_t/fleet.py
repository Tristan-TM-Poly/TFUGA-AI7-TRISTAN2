from __future__ import annotations

import hashlib
import hmac
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from .query import query_payload


def _token(secret: str, value: str, *, prefix: str) -> str:
    if not secret:
        raise ValueError("fleet salt must be non-empty")
    digest = hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{prefix}_{digest[:20]}"


def _proof_debt(metrics: Mapping[str, Any]) -> int:
    documented = bool(metrics.get("documented") or int(metrics.get("documents", 0) or 0))
    implemented = bool(metrics.get("implemented") or int(metrics.get("code_files", 0) or 0))
    tested = bool(metrics.get("tested") or int(metrics.get("tests", 0) or 0))
    linked_ci = bool(int(metrics.get("workflows", 0) or 0))
    schema_backed = bool(metrics.get("schema_backed") or int(metrics.get("schemas", 0) or 0))
    missing = int(not documented) + int(not implemented)
    if implemented:
        missing += int(not tested) + int(not linked_ci) + int(not schema_backed)
    return missing


def _fingerprint(repositories: list[dict[str, Any]], totals: Mapping[str, Any], source_kind: str) -> str:
    raw = json.dumps(
        {"repositories": repositories, "totals": totals, "source_kind": source_kind},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_fleet_manifest(
    source: str | Path | Mapping[str, Any],
    *,
    salt: str,
) -> dict[str, Any]:
    """Build a publishable organization/fleet projection without raw repository names.

    The salt is supplied at runtime and is never serialized. Repository tokens and
    the fleet identifier are stable only for the same salt. System names and paths
    are intentionally omitted from the public projection; only aggregate structural
    metrics are retained.
    """

    report = query_payload(source, kind="system", limit=1_000_000)
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in report.get("results", []):
        by_repo[str(item.get("repository", ""))].append(dict(item))

    repositories: list[dict[str, Any]] = []
    global_status = Counter()
    total_systems = 0
    total_crystallization = 0.0
    total_debt = 0
    attention = Counter()

    for repository in sorted(by_repo):
        systems = by_repo[repository]
        status_counts = Counter(str(item.get("status", "observed")) for item in systems)
        crystallizations = [float(item.get("structural_crystallization") or 0.0) for item in systems]
        debts = [_proof_debt(item.get("metrics", {})) for item in systems]
        repo_attention = Counter()
        for item in systems:
            metrics = item.get("metrics", {})
            implemented = bool(metrics.get("implemented") or int(metrics.get("code_files", 0) or 0))
            tested = bool(metrics.get("tested") or int(metrics.get("tests", 0) or 0))
            linked_ci = bool(int(metrics.get("workflows", 0) or 0))
            schema_backed = bool(metrics.get("schema_backed") or int(metrics.get("schemas", 0) or 0))
            if implemented and not tested:
                repo_attention["implemented_without_tests"] += 1
            if implemented and not linked_ci:
                repo_attention["implemented_without_linked_ci"] += 1
            if implemented and not schema_backed:
                repo_attention["implemented_without_machine_contract"] += 1
        repo_token = _token(salt, repository, prefix="repo")
        repositories.append(
            {
                "repository_token": repo_token,
                "systems": len(systems),
                "status_counts": dict(sorted(status_counts.items())),
                "mean_structural_crystallization": round(sum(crystallizations) / len(systems), 4) if systems else 0.0,
                "mean_structural_proof_debt": round(sum(debts) / len(systems), 4) if systems else 0.0,
                "attention": dict(sorted(repo_attention.items())),
            }
        )
        global_status.update(status_counts)
        total_systems += len(systems)
        total_crystallization += sum(crystallizations)
        total_debt += sum(debts)
        attention.update(repo_attention)

    # Fleet identity is tied to the private runtime salt, not to the current
    # repository membership. Adding/removing a repository therefore changes the
    # snapshot fingerprint without destroying longitudinal fleet continuity.
    fleet_id = _token(salt, "omega-summary-fleet-v1", prefix="fleet")
    totals = {
        "repositories": len(repositories),
        "systems": total_systems,
        "status_counts": dict(sorted(global_status.items())),
        "mean_structural_crystallization": round(total_crystallization / total_systems, 4) if total_systems else 0.0,
        "mean_structural_proof_debt": round(total_debt / total_systems, 4) if total_systems else 0.0,
        "attention": dict(sorted(attention.items())),
    }
    source_kind = str(report.get("source_kind", "unknown"))
    return {
        "schema_version": "1.0.0",
        "fleet_id": fleet_id,
        "fingerprint": _fingerprint(repositories, totals, source_kind),
        "source_kind": source_kind,
        "repositories": repositories,
        "totals": totals,
        "privacy": {
            "raw_repository_names_serialized": False,
            "raw_system_names_serialized": False,
            "repository_token_algorithm": "HMAC-SHA256-truncated-20hex",
            "salt_serialized": False,
            "salt_required_at_runtime": True,
            "salt_rotation_breaks_token_continuity": True,
        },
        "boundary": "fleet aggregates describe repository structure only; pseudonymized tokens are not identities, security boundaries, ownership claims, scientific rankings or commercial rankings",
    }


def _history_hash(report: Mapping[str, Any], previous_hash: str) -> str:
    raw = json.dumps(
        {"previous_hash": previous_hash, "report": report},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_fleet_history(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {
            "schema_version": "1.0.0",
            "fleet_id": "",
            "runs": [],
            "privacy": {"contains_raw_repository_names": False, "contains_salt": False},
            "boundary": "hash-chained pseudonymized fleet history; structural observations only",
        }
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("runs"), list):
        raise ValueError("invalid fleet history")
    return payload


def verify_fleet_history(history: Mapping[str, Any]) -> bool:
    previous_hash = ""
    fleet_id = str(history.get("fleet_id", ""))
    for ordinal, item in enumerate(history.get("runs", []), start=1):
        if int(item.get("ordinal", 0)) != ordinal:
            return False
        if str(item.get("previous_hash", "")) != previous_hash:
            return False
        report = item.get("report", {})
        if fleet_id and str(report.get("fleet_id", "")) != fleet_id:
            return False
        expected = _history_hash(report, previous_hash)
        if str(item.get("entry_hash", "")) != expected:
            return False
        previous_hash = expected
    return True


def append_fleet_history(path: str | Path, report: Mapping[str, Any]) -> dict[str, Any]:
    history = load_fleet_history(path)
    if not verify_fleet_history(history):
        raise ValueError("fleet history hash chain is invalid")
    fleet_id = str(report.get("fleet_id", ""))
    if history.get("fleet_id") and history.get("fleet_id") != fleet_id:
        raise ValueError("fleet_id changed; the HMAC salt/scope changed, start a new fleet history")
    if any(item.get("report", {}).get("fingerprint") == report.get("fingerprint") for item in history.get("runs", [])):
        return history
    previous_hash = str(history["runs"][-1]["entry_hash"]) if history["runs"] else ""
    history["fleet_id"] = fleet_id
    entry_hash = _history_hash(report, previous_hash)
    history["runs"].append(
        {
            "ordinal": len(history["runs"]) + 1,
            "previous_hash": previous_hash,
            "entry_hash": entry_hash,
            "report": dict(report),
        }
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(history, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return history


def render_fleet_markdown(report: Mapping[str, Any]) -> str:
    totals = report.get("totals", {})
    lines = [
        "# Ω-SUMMARY FLEET OBSERVATORY",
        "",
        f"- fleet : `{report.get('fleet_id', '')}`",
        f"- fingerprint : `{report.get('fingerprint', '')}`",
        f"- dépôts pseudonymisés : **{totals.get('repositories', 0)}**",
        f"- systèmes observés : **{totals.get('systems', 0)}**",
        f"- C_struct moyen : **{float(totals.get('mean_structural_crystallization', 0.0)):.3f}**",
        f"- dette structurelle moyenne : **{float(totals.get('mean_structural_proof_debt', 0.0)):.3f}**",
        "",
        "| Repository token | Systèmes | C_struct | Dette | Statuts |",
        "|---|---:|---:|---:|---|",
    ]
    for item in report.get("repositories", []):
        statuses = ", ".join(f"{key}:{value}" for key, value in item.get("status_counts", {}).items())
        lines.append(
            f"| `{item.get('repository_token', '')}` | {item.get('systems', 0)} | "
            f"{float(item.get('mean_structural_crystallization', 0.0)):.3f} | "
            f"{float(item.get('mean_structural_proof_debt', 0.0)):.3f} | {statuses} |"
        )
    if not report.get("repositories"):
        lines.append("| — | 0 | 0 | 0 | — |")
    lines += [
        "",
        "## Privacy invariant",
        "",
        "Les noms bruts de dépôts et de systèmes ne sont pas sérialisés dans cette projection publique. Le sel HMAC reste hors artefact. Une rotation de sel crée volontairement une nouvelle identité de flotte.",
        "",
        "## OAK boundary",
        "",
        str(report.get("boundary", "")),
        "",
    ]
    return "\n".join(lines)


def render_fleet_html(report: Mapping[str, Any]) -> str:
    """Render a dependency-free static dashboard; no raw repository names are embedded."""

    rows = []
    for item in report.get("repositories", []):
        statuses = " ".join(f"{key}:{value}" for key, value in item.get("status_counts", {}).items())
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(item.get('repository_token', '')))}</code></td>"
            f"<td>{int(item.get('systems', 0))}</td>"
            f"<td>{float(item.get('mean_structural_crystallization', 0.0)):.3f}</td>"
            f"<td>{float(item.get('mean_structural_proof_debt', 0.0)):.3f}</td>"
            f"<td>{html.escape(statuses)}</td>"
            "</tr>"
        )
    totals = report.get("totals", {})
    boundary = html.escape(str(report.get("boundary", "")))
    return f"""<!doctype html>
<html lang="fr">
<meta charset="utf-8">
<title>Ω-SUMMARY Fleet Observatory</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;line-height:1.45}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}}
.card{{border:1px solid #bbb;border-radius:12px;padding:1rem}}table{{width:100%;border-collapse:collapse;margin-top:1rem}}
th,td{{border-bottom:1px solid #ddd;text-align:left;padding:.55rem}}input{{width:100%;padding:.6rem;margin:1rem 0}}
small{{opacity:.75}}
</style>
<h1>Ω-SUMMARY Fleet Observatory</h1>
<div class="cards">
<div class="card"><b>Dépôts</b><br>{int(totals.get('repositories', 0))}</div>
<div class="card"><b>Systèmes</b><br>{int(totals.get('systems', 0))}</div>
<div class="card"><b>C_struct moyen</b><br>{float(totals.get('mean_structural_crystallization', 0.0)):.3f}</div>
<div class="card"><b>Dette moyenne</b><br>{float(totals.get('mean_structural_proof_debt', 0.0)):.3f}</div>
</div>
<input id="filter" placeholder="Filtrer par token/statut" oninput="filterRows()">
<table id="fleet"><thead><tr><th>Repository token</th><th>Systèmes</th><th>C_struct</th><th>Dette</th><th>Statuts</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Privacy/OAK</h2><p>Aucun nom brut de dépôt ou système n'est embarqué. Le sel HMAC n'est pas sérialisé.</p><small>{boundary}</small>
<script>
function filterRows(){{const q=document.getElementById('filter').value.toLowerCase();for(const row of document.querySelectorAll('#fleet tbody tr')){{row.style.display=row.innerText.toLowerCase().includes(q)?'':'none';}}}}
</script>
</html>"""


def write_fleet_manifest(
    source: str | Path | Mapping[str, Any],
    output_dir: str | Path,
    *,
    salt: str,
) -> dict[str, Path]:
    report = build_fleet_manifest(source, salt=salt)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "FLEET_PUBLIC.json"
    markdown_path = out / "FLEET_PUBLIC.md"
    html_path = out / "FLEET_DASHBOARD.html"
    history_path = out / "FLEET_HISTORY.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_fleet_markdown(report), encoding="utf-8")
    html_path.write_text(render_fleet_html(report), encoding="utf-8")
    history = append_fleet_history(history_path, report)
    if not verify_fleet_history(history):
        raise ValueError("fleet history hash chain is invalid after append")
    return {
        "fleet_json": json_path,
        "fleet_markdown": markdown_path,
        "fleet_html": html_path,
        "fleet_history": history_path,
    }
