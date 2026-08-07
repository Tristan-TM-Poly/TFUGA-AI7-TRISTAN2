from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _load_payload(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _systems(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(node["path"]): dict(node)
        for node in payload.get("nodes", [])
        if node.get("kind") == "system" and node.get("path")
    }


def _evidence_hashes(node: Mapping[str, Any]) -> set[str]:
    hashes = set()
    for evidence in node.get("evidence", []):
        digest = str(evidence.get("sha256", "")).strip()
        if digest:
            hashes.add(digest)
    return hashes


def content_signature(node: Mapping[str, Any]) -> str:
    """Path-independent signature from observed evidence hashes.

    The signature is evidence for continuity, not proof of identity: copied or
    vendored systems may legitimately have the same content.
    """

    hashes = sorted(_evidence_hashes(node))
    if not hashes:
        return ""
    raw = json.dumps(hashes, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def resolve_identity(
    previous: str | Path | Mapping[str, Any],
    current: str | Path | Mapping[str, Any],
    *,
    min_overlap: float = 0.80,
) -> dict[str, Any]:
    """Find review-only rename/move candidates across two repository snapshots."""

    before = _load_payload(previous)
    after = _load_payload(current)
    before_systems = _systems(before)
    after_systems = _systems(after)
    removed = sorted(set(before_systems) - set(after_systems))
    added = sorted(set(after_systems) - set(before_systems))

    candidates: list[dict[str, Any]] = []
    for old_name in removed:
        old = before_systems[old_name]
        old_hashes = _evidence_hashes(old)
        old_signature = content_signature(old)
        if not old_hashes:
            continue
        for new_name in added:
            new = after_systems[new_name]
            new_hashes = _evidence_hashes(new)
            if not new_hashes:
                continue
            new_signature = content_signature(new)
            union = old_hashes | new_hashes
            overlap = len(old_hashes & new_hashes) / len(union) if union else 0.0
            exact = bool(old_signature and old_signature == new_signature)
            if not exact and overlap < min_overlap:
                continue
            candidates.append(
                {
                    "from": old_name,
                    "to": new_name,
                    "score": 1.0 if exact else round(overlap, 4),
                    "evidence": "exact_content_signature" if exact else "evidence_hash_jaccard",
                    "shared_evidence_hashes": len(old_hashes & new_hashes),
                    "previous_evidence_hashes": len(old_hashes),
                    "current_evidence_hashes": len(new_hashes),
                    "previous_signature": old_signature,
                    "current_signature": new_signature,
                    "classification": "rename-or-move-candidate",
                    "status": "review_required",
                    "automatic_rewrite": False,
                }
            )

    by_old: dict[str, int] = {}
    by_new: dict[str, int] = {}
    for item in candidates:
        by_old[item["from"]] = by_old.get(item["from"], 0) + 1
        by_new[item["to"]] = by_new.get(item["to"], 0) + 1
    for item in candidates:
        item["one_to_one"] = by_old[item["from"]] == 1 and by_new[item["to"]] == 1

    candidates.sort(key=lambda item: (-float(item["score"]), item["from"], item["to"]))
    return {
        "schema_version": "1.0.0",
        "previous_fingerprint": before.get("cache_fingerprint", ""),
        "current_fingerprint": after.get("cache_fingerprint", ""),
        "removed_systems": removed,
        "added_systems": added,
        "candidates": candidates,
        "boundary": "content-addressed continuity candidates are review-only; identical content can be copied, forked or vendored and does not prove semantic identity, authorship, novelty or IP continuity",
    }


def render_identity_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# IDENTITY CONTINUITY",
        "",
        f"- précédent : `{report.get('previous_fingerprint', '')}`",
        f"- courant : `{report.get('current_fingerprint', '')}`",
        f"- systèmes retirés : **{len(report.get('removed_systems', []))}**",
        f"- systèmes ajoutés : **{len(report.get('added_systems', []))}**",
        f"- candidats : **{len(report.get('candidates', []))}**",
        "",
        "| Ancien | Nouveau | Score | Preuve | 1→1 | Action |",
        "|---|---|---:|---|---:|---|",
    ]
    for item in report.get("candidates", []):
        lines.append(
            f"| `{item['from']}` | `{item['to']}` | {item['score']:.3f} | {item['evidence']} | "
            f"{'yes' if item.get('one_to_one') else 'no'} | review_required |"
        )
    if not report.get("candidates"):
        lines.append("| — | — | — | aucun candidat | — | — |")
    lines += ["", "## OAK boundary", "", str(report.get("boundary", "")), ""]
    return "\n".join(lines)


def write_identity_report(
    previous: str | Path | Mapping[str, Any],
    current: str | Path | Mapping[str, Any],
    output_dir: str | Path,
    *,
    min_overlap: float = 0.80,
) -> dict[str, Path]:
    report = resolve_identity(previous, current, min_overlap=min_overlap)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "IDENTITY_CONTINUITY.json"
    markdown_path = out / "IDENTITY_CONTINUITY.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_identity_markdown(report), encoding="utf-8")
    return {"identity_json": json_path, "identity_markdown": markdown_path}
