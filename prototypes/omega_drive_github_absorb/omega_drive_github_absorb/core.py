from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Literal
from urllib.parse import parse_qs, urlparse

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

LEVEL_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5, "L6": 6, "L7": 7}


@dataclasses.dataclass(frozen=True)
class DriveObject:
    source_url: str
    drive_id: str | None
    kind: DriveKind
    requires_oauth: bool = True
    owner_visibility: str = "unknown"
    risk_level: str = "medium"
    normalized_url: str | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class PermissionPolicy:
    """OAK gate for Drive→GitHub absorption.

    The defaults are intentionally conservative. A caller must explicitly choose
    higher levels and enable download/publication behaviors. Even then, L7 public
    release remains blocked unless external human/IP review is represented by a
    separate signed policy layer.
    """

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
        if requested_level not in LEVEL_ORDER:
            return "BLOCK_PUBLICATION"
        if LEVEL_ORDER[requested_level] > LEVEL_ORDER.get(self.max_level, 1):
            return "BLOCK_DOWNLOAD" if requested_level in {"L2", "L3"} else "BLOCK_PUBLICATION"
        if self.allow_delete or self.allow_permission_change or self.allow_push_to_default_branch:
            return "BLOCK_PUBLICATION"
        if requested_level in {"L0", "L1"}:
            return "ALLOW_INVENTORY_ONLY"
        if requested_level in {"L2", "L3"}:
            return "ALLOW_PRIVATE_SYNC" if self.allow_download else "BLOCK_DOWNLOAD"
        if requested_level in {"L4", "L5", "L6"}:
            return "ALLOW_BRANCH_ONLY"
        if requested_level == "L7":
            return "REQUIRES_IP_REVIEW" if self.require_ip_review else "BLOCK_PUBLICATION"
        return "BLOCK_PUBLICATION"


class DriveLinkResolver:
    """Resolve Google Drive/Docs URLs into typed objects without network access."""

    PATTERNS: tuple[tuple[DriveKind, re.Pattern[str]], ...] = (
        ("folder", re.compile(r"drive\.google\.com/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)")),
        ("file", re.compile(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)")),
        ("doc", re.compile(r"docs\.google\.com/document/d/([A-Za-z0-9_-]+)")),
        ("sheet", re.compile(r"docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)")),
        ("slides", re.compile(r"docs\.google\.com/presentation/d/([A-Za-z0-9_-]+)")),
    )

    @classmethod
    def resolve(cls, url: str) -> DriveObject:
        clean = url.strip()
        normalized = cls.normalize(clean)
        for kind, pattern in cls.PATTERNS:
            match = pattern.search(normalized)
            if match:
                return DriveObject(
                    source_url=clean,
                    normalized_url=normalized,
                    drive_id=match.group(1),
                    kind=kind,
                    risk_level="medium",
                )

        parsed = urlparse(normalized)
        query_id = parse_qs(parsed.query).get("id", [None])[0]
        if parsed.netloc.endswith("drive.google.com") and query_id:
            return DriveObject(
                source_url=clean,
                normalized_url=normalized,
                drive_id=query_id,
                kind="file",
                risk_level="medium",
            )

        return DriveObject(
            source_url=clean,
            normalized_url=normalized,
            drive_id=None,
            kind="unknown",
            risk_level="high",
        )

    @staticmethod
    def normalize(url: str) -> str:
        if not url:
            return url
        if url.startswith("http://"):
            return "https://" + url[len("http://") :]
        return url


class OakSecurityScanner:
    """Lightweight metadata scanner.

    This scanner is not a replacement for secret scanning on downloaded content.
    It flags risky URLs/names before the heavier extraction layer is allowed.
    """

    SECRETISH_PATTERNS = (
        re.compile(r"token", re.IGNORECASE),
        re.compile(r"secret", re.IGNORECASE),
        re.compile(r"password", re.IGNORECASE),
        re.compile(r"credential", re.IGNORECASE),
        re.compile(r"private", re.IGNORECASE),
        re.compile(r"api[_-]?key", re.IGNORECASE),
    )

    @classmethod
    def scan_drive_object(cls, obj: DriveObject) -> dict:
        flags = []
        for pattern in cls.SECRETISH_PATTERNS:
            if pattern.search(obj.source_url):
                flags.append(f"url_matches:{pattern.pattern}")
        if obj.kind == "unknown":
            flags.append("unknown_drive_link_format")
        return {
            "source_url_sha256": sha256_text(obj.source_url),
            "kind": obj.kind,
            "risk_level": "high" if flags else obj.risk_level,
            "flags": flags,
            "recommended_verdict": "REQUIRES_REDACTION" if flags else "ALLOW_INVENTORY_ONLY",
        }


class ManifestBuilder:
    @staticmethod
    def build(objects: Iterable[DriveObject], policy: PermissionPolicy, requested_level: str = "L1") -> list[dict]:
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        rows: list[dict] = []
        for obj in objects:
            scan = OakSecurityScanner.scan_drive_object(obj)
            url_hash = sha256_text(obj.source_url)
            rows.append(
                {
                    "source_url": obj.source_url,
                    "source_url_sha256": url_hash,
                    "normalized_url": obj.normalized_url,
                    "drive_file_id": obj.drive_id,
                    "kind": obj.kind,
                    "mime_type": None,
                    "size_bytes": None,
                    "sha256": None,
                    "downloaded_at": None,
                    "inventoried_at": now,
                    "extraction_method": None,
                    "oak_status": policy.gate(requested_level),
                    "scanner_flags": scan["flags"],
                    "github_target": f"generated/drive/{obj.drive_id or url_hash[:12]}",
                    "risk_level": scan["risk_level"],
                    "requires_oauth": obj.requires_oauth,
                }
            )
        return rows


class HypergraphBuilder:
    @staticmethod
    def from_manifest(manifest: list[dict]) -> dict:
        nodes: list[dict] = []
        edges: list[dict] = []
        for row in manifest:
            file_node = f"drive:{row.get('drive_file_id') or row['source_url_sha256'][:12]}"
            url_node = f"url:{row['source_url_sha256'][:12]}"
            oak_node = f"oak:{row['oak_status']}"
            kind_node = f"kind:{row['kind']}"
            nodes.extend(
                [
                    {"id": file_node, "type": "drive_object", "risk_level": row["risk_level"]},
                    {"id": url_node, "type": "source_url_hash"},
                    {"id": oak_node, "type": "oak_verdict"},
                    {"id": kind_node, "type": "drive_kind"},
                ]
            )
            edges.extend(
                [
                    {"source": file_node, "target": url_node, "type": "has_source"},
                    {"source": file_node, "target": oak_node, "type": "has_oak_status"},
                    {"source": file_node, "target": kind_node, "type": "has_kind"},
                ]
            )
            for flag in row.get("scanner_flags", []):
                flag_node = f"m_minus:{sha256_text(flag)[:12]}"
                nodes.append({"id": flag_node, "type": "m_minus_flag", "label": flag})
                edges.append({"source": file_node, "target": flag_node, "type": "has_risk_flag"})
        return dedupe_graph({"nodes": nodes, "edges": edges})


class GitHubSyncPlanner:
    @staticmethod
    def build_plan(manifest: list[dict], repo: str, branch_prefix: str = "omega-drive-github-absorb") -> dict:
        risky = [row for row in manifest if row.get("risk_level") == "high"]
        return {
            "repo": repo,
            "mode": "dry-run",
            "branch_policy": "dedicated branch only",
            "branch_prefix": branch_prefix,
            "default_branch_push": False,
            "public_release": False,
            "objects_count": len(manifest),
            "high_risk_objects_count": len(risky),
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
            "next_actions": [
                "Authenticate with least-privilege Google Drive OAuth readonly scope.",
                "Download only after PermissionGate allows L2.",
                "Compute real sha256 after download.",
                "Extract PDF/ZIP/DOCX into page-level or file-level chunks.",
                "Run OAK security/IP scan before public GitHub publication.",
                "Open draft PR; never auto-merge.",
            ],
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dedupe_graph(graph: dict) -> dict:
    seen_nodes = set()
    nodes = []
    for node in graph["nodes"]:
        node_id = node["id"]
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append(node)
    seen_edges = set()
    edges = []
    for edge in graph["edges"]:
        key = (edge["source"], edge["target"], edge["type"])
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(edge)
    return {"nodes": nodes, "edges": edges}


def read_links(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
