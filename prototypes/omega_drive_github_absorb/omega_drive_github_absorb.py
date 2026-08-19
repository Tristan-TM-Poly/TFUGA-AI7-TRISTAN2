#!/usr/bin/env python3
"""
Ω-DRIVE-GITHUB-ABSORB-T — MVP OAK-safe

Prototype local pour inventorier des liens Google Drive, générer des manifestes,
préparer une absorption GitHub, et refuser toute action dangereuse par défaut.

Ce script ne télécharge pas réellement les fichiers sans implémentation OAuth explicite.
Il pose le squelette sûr : résolution de liens, policy gate, manifest, provenance,
plan GitHub et rapports OAK.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Literal

DriveKind = Literal["file", "folder", "doc", "sheet", "slides", "unknown"]
OakVerdict = Literal[
    "ALLOW_INVENTORY_ONLY",
    "ALLOW_PRIVATE_SYNC",
    "ALLOW_BRANCH_ONLY",
    "REQUIRES_REDACTION",
    "REQUIRES_IP_REVIEW",
    "BLOCK_PUBLICATION",
    "BLOCK_DOWNLOAD",
]


@dataclasses.dataclass(frozen=True)
class DriveObject:
    source_url: str
    drive_id: str | None
    kind: DriveKind
    requires_oauth: bool = True
    owner_visibility: str = "unknown"
    risk_level: str = "medium"


@dataclasses.dataclass(frozen=True)
class PermissionPolicy:
    mode: str = "dry-run"
    max_level: str = "L1"
    allow_download: bool = False
    allow_publication: bool = False
    allow_delete: bool = False
    allow_permission_change: bool = False
    allow_push_to_default_branch: bool = False
    require_ip_review: bool = True
    require_oak_report: bool = True

    def gate(self, requested_level: str) -> OakVerdict:
        dangerous = [
            self.allow_publication,
            self.allow_delete,
            self.allow_permission_change,
            self.allow_push_to_default_branch,
        ]
        if any(dangerous):
            return "BLOCK_PUBLICATION"
        if requested_level in {"L0", "L1"}:
            return "ALLOW_INVENTORY_ONLY"
        if requested_level in {"L2", "L3"} and not self.allow_download:
            return "BLOCK_DOWNLOAD"
        if requested_level in {"L4", "L5", "L6"}:
            return "ALLOW_BRANCH_ONLY"
        return "REQUIRES_IP_REVIEW"


class DriveLinkResolver:
    patterns = [
        ("folder", re.compile(r"drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)")),
        ("file", re.compile(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)")),
        ("doc", re.compile(r"docs\.google\.com/document/d/([A-Za-z0-9_-]+)")),
        ("sheet", re.compile(r"docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)")),
        ("slides", re.compile(r"docs\.google\.com/presentation/d/([A-Za-z0-9_-]+)")),
    ]

    @classmethod
    def resolve(cls, url: str) -> DriveObject:
        clean = url.strip()
        for kind, pattern in cls.patterns:
            match = pattern.search(clean)
            if match:
                return DriveObject(source_url=clean, drive_id=match.group(1), kind=kind)  # type: ignore[arg-type]
        return DriveObject(source_url=clean, drive_id=None, kind="unknown", risk_level="high")


class ManifestBuilder:
    @staticmethod
    def build(objects: Iterable[DriveObject], policy: PermissionPolicy) -> list[dict]:
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        rows: list[dict] = []
        for obj in objects:
            synthetic_hash = hashlib.sha256(obj.source_url.encode("utf-8")).hexdigest()
            rows.append(
                {
                    "source_url": obj.source_url,
                    "drive_file_id": obj.drive_id,
                    "kind": obj.kind,
                    "mime_type": None,
                    "size_bytes": None,
                    "sha256": None,
                    "url_sha256": synthetic_hash,
                    "downloaded_at": None,
                    "inventoried_at": now,
                    "extraction_method": None,
                    "oak_status": policy.gate("L1"),
                    "github_target": f"generated/drive/{obj.drive_id or synthetic_hash[:12]}",
                    "risk_level": obj.risk_level,
                    "requires_oauth": obj.requires_oauth,
                }
            )
        return rows


class GitHubSyncPlanner:
    @staticmethod
    def build_plan(manifest: list[dict], repo: str) -> dict:
        return {
            "repo": repo,
            "mode": "dry-run",
            "branch_policy": "dedicated branch only",
            "default_branch_push": False,
            "planned_paths": {
                "manifest": "manifest/drive_manifest.json",
                "provenance": "manifest/provenance_ledger.jsonl",
                "chunks": "corpus/extracted_chunks.jsonl",
                "theory_graph": "hypergraphs/theory_graph.json",
                "claim_evidence_graph": "hypergraphs/claim_evidence_graph.json",
                "oak_report": "oak/oak_report.md",
                "security_report": "oak/security_report.md",
                "ip_report": "oak/ip_report.md",
            },
            "objects_count": len(manifest),
            "next_actions": [
                "Authenticate with least-privilege Google Drive OAuth scope.",
                "Download only after PermissionGate allows L2.",
                "Compute sha256 after download.",
                "Extract PDF/ZIP/DOCX into page-level or file-level chunks.",
                "Run OAK security/IP scan before any public GitHub publication.",
                "Open a draft PR; never auto-merge.",
            ],
        }


def read_links(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ω-DRIVE-GITHUB-ABSORB-T MVP dry-run planner")
    parser.add_argument("links_file", type=Path, help="Text file containing Google Drive links, one per line")
    parser.add_argument("--repo", default="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2", help="GitHub repo target")
    parser.add_argument("--out", type=Path, default=Path("generated/omega_drive_github_absorb"), help="Output folder")
    parser.add_argument("--level", default="L1", choices=["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"], help="Requested OAK level")
    parser.add_argument("--allow-download", action="store_true", help="Allow L2/L3 download planning; still requires OAuth implementation")
    args = parser.parse_args()

    policy = PermissionPolicy(max_level=args.level, allow_download=args.allow_download)
    verdict = policy.gate(args.level)

    links = read_links(args.links_file)
    objects = [DriveLinkResolver.resolve(url) for url in links]
    manifest = ManifestBuilder.build(objects, policy)
    plan = GitHubSyncPlanner.build_plan(manifest, args.repo)

    oak_report = {
        "system": "Ω-DRIVE-GITHUB-ABSORB-T",
        "requested_level": args.level,
        "verdict": verdict,
        "dangerous_actions_blocked": True,
        "publication_allowed": False,
        "delete_allowed": False,
        "permission_change_allowed": False,
        "default_branch_push_allowed": False,
        "objects_count": len(objects),
        "unknown_links": [obj.source_url for obj in objects if obj.kind == "unknown"],
    }

    write_json(args.out / "drive_manifest.json", manifest)
    write_json(args.out / "github_sync_plan.json", plan)
    write_json(args.out / "oak_report.json", oak_report)

    print(json.dumps(oak_report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
