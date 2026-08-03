"""Multi-type Grand Atlas and repository-backed canonical memory for R0.2."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .core import Snapshot, digest

ARTIFACT_TYPES = {
    "CAMPAIGN", "DATASET", "ENGINE", "EVIDENCE_SYSTEM", "FOUNDRY",
    "GOVERNANCE", "KERNEL", "LAB", "MEMORY", "OS", "PRODUCT",
    "PROTOTYPE", "REPOSITORY", "SERVICE", "THEORY", "VENTURE",
}

CANONICAL_MEMORY = (
    "The 23-object R0.1 portfolio is a seed showcase, never an exhaustive inventory.",
    "Future portfolio analysis starts from the multi-type Grand Atlas and preserves the R0.1 lineage.",
    "Distinguish family, system, version, module, campaign, dataset, product, service, venture and repository.",
    "Distinguish open, draft, stacked, merged, integrated, alive, used and valuable.",
    "Distinguish logical, planned, materialized, executed, software-verified, externally evaluated, externally replicated and product-used.",
    "Generated size, line count, tests and address capacity never substitute for unique verified behavior, fair baselines, users, payments or retention.",
    "Under-verified capabilities remain STRUCTURED or DECLARED; absence from the atlas never means absence from GitHub.",
    "No summary may claim all best work without a fresh all-repository, all-branch and all-PR audit.",
    "Every major portfolio session should close one concrete artifact, one OAK result and one next action.",
    "Merge, release, publication, deployment, spending, IP filing, external messaging and destructive action remain human decisions.",
)


@dataclass(frozen=True)
class AtlasMetadata:
    artifact_type: str
    family: str
    level: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _tag_value(tags: Iterable[str], prefix: str, default: str) -> str:
    for tag in tags:
        if tag.startswith(prefix):
            return tag[len(prefix):]
    return default


def metadata(item: Any) -> AtlasMetadata:
    artifact_type = _tag_value(item.tags, "type:", "PROTOTYPE")
    family = _tag_value(item.tags, "family:", "legacy-r0.1")
    level = _tag_value(item.tags, "level:", item.claim.status)
    if artifact_type not in ARTIFACT_TYPES:
        raise ValueError(f"unknown Grand Atlas artifact type: {artifact_type}")
    return AtlasMetadata(artifact_type, family, level, f"{item.repository}@{item.ref}")


def grand_atlas_report(snapshot: Snapshot) -> dict[str, Any]:
    rows = []
    family_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    repository_counts: Counter[str] = Counter()
    for item in sorted(snapshot.prototypes, key=lambda record: record.prototype_id):
        meta = metadata(item)
        family_counts[meta.family] += 1
        type_counts[meta.artifact_type] += 1
        level_counts[meta.level] += 1
        repository_counts[item.repository] += 1
        rows.append({
            "prototype_id": item.prototype_id,
            "name": item.name,
            "category": item.category,
            "repository": item.repository,
            "ref": item.ref,
            "artifact_type": meta.artifact_type,
            "family": meta.family,
            "level": meta.level,
            "claim_status": item.claim.status,
            "strongest_evidence": max(
                ("DECLARED", "OBSERVED", "REPRODUCED", "INDEPENDENT").index(e.strength)
                for e in item.evidence
            ),
            "source": meta.source,
            "next_action": asdict(item.next_action),
        })
    report: dict[str, Any] = {
        "atlas_id": "omega-grand-atlas-tristan-r0.2",
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_sha256": snapshot.sha256,
        "entry_count": len(rows),
        "legacy_r01_count": family_counts.get("legacy-r0.1", 0),
        "family_count": len(family_counts),
        "artifact_type_count": len(type_counts),
        "declared_only_count": sum(
            all(e.strength == "DECLARED" for e in item.evidence)
            for item in snapshot.prototypes
        ),
        "family_counts": dict(sorted(family_counts.items())),
        "artifact_type_counts": dict(sorted(type_counts.items())),
        "level_counts": dict(sorted(level_counts.items())),
        "repository_counts": dict(sorted(repository_counts.items())),
        "entries": rows,
        "canonical_memory": list(CANONICAL_MEMORY),
        "exhaustiveness_claimed": False,
        "truth_probability_claimed": False,
        "external_action_performed": False,
        "merge_authorized": False,
        "publication_authorized": False,
    }
    report["atlas_sha256"] = digest(report)
    return report


def memory_markdown(snapshot: Snapshot) -> str:
    report = grand_atlas_report(snapshot)
    lines = [
        "# Ω-GRAND-ATLAS-TRISTAN-T∞ — Canonical Memory R0.2",
        "",
        f"Snapshot: `{snapshot.snapshot_id}`",
        f"Entries: **{report['entry_count']}**",
        f"Families: **{report['family_count']}**",
        f"Artifact types: **{report['artifact_type_count']}**",
        "",
        "## Persistent rules",
        "",
    ]
    lines.extend(f"{index}. {rule}" for index, rule in enumerate(CANONICAL_MEMORY, 1))
    lines.extend([
        "",
        "## OAK boundary",
        "",
        "- registry pointer != live repository truth",
        "- open PR != merged capability",
        "- merged capability != current-main survivance",
        "- internal tests != independent validation",
        "- product hypothesis != user, payment or retention",
        "- this atlas is intentionally non-exhaustive and refreshable",
        "",
    ])
    return "\n".join(lines)


def compile_grand_atlas(snapshot: Snapshot, output_dir: str | Path) -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    report = grand_atlas_report(snapshot)
    entries_jsonl = "".join(
        json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n"
        for entry in report["entries"]
    )
    payloads = {
        "grand_atlas.json": json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "atlas_entries.jsonl": entries_jsonl,
        "CANONICAL_MEMORY.md": memory_markdown(snapshot),
    }
    receipts = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in payloads.items()
    }
    manifest = {
        "atlas_sha256": report["atlas_sha256"],
        "snapshot_sha256": snapshot.sha256,
        "files": dict(sorted(receipts.items())),
        "entry_count": report["entry_count"],
        "family_count": report["family_count"],
        "artifact_type_count": report["artifact_type_count"],
        "exhaustiveness_claimed": False,
        "external_action_performed": False,
    }
    manifest["manifest_sha256"] = digest(manifest)
    payloads["manifest.json"] = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    for name, content in payloads.items():
        (root / name).write_text(content, encoding="utf-8")
    receipts["manifest.json"] = hashlib.sha256(payloads["manifest.json"].encode("utf-8")).hexdigest()
    return dict(sorted(receipts.items()))
