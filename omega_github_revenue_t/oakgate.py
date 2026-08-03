from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .authorization import AuditAuthorization
from .repository_audit import (
    AuditPolicy,
    RepositoryAuditReport,
    audit_repository,
    write_report_bundle,
)
from .transparency import build_manifest, digest_payload


@dataclass(frozen=True)
class OAKGateRunReceipt:
    run_id: str
    repository_id: str
    authorization_id: str
    report_hash: str
    manifest_hash: str
    merkle_root: str
    files_in_bundle: int
    external_actions: tuple[str, ...]
    non_claims: tuple[str, ...]
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_oakgate(
    repository_root: str | Path,
    authorization: AuditAuthorization,
    output_dir: str | Path,
    *,
    policy: AuditPolicy | None = None,
) -> tuple[RepositoryAuditReport, OAKGateRunReceipt]:
    report = audit_repository(repository_root, authorization, policy=policy)
    destination = Path(output_dir)
    bundle = write_report_bundle(report, destination)
    authorization_path = destination / "authorization-receipt.json"
    authorization_path.write_text(
        json.dumps(
            authorization.to_public_receipt(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = build_manifest(
        destination,
        [bundle["json"], bundle["markdown"], authorization_path],
    )
    manifest_path = destination / "evidence-manifest.json"
    manifest_path.write_text(
        json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    run_id = f"OAKRUN-{report.report_hash[:16]}"
    body = {
        "run_id": run_id,
        "repository_id": report.repository_id,
        "authorization_id": report.authorization_id,
        "report_hash": report.report_hash,
        "manifest_hash": manifest.manifest_hash,
        "merkle_root": manifest.merkle_root,
        "files_in_bundle": len(manifest.entries),
        "external_actions": [],
        "non_claims": [
            "no repository mutation",
            "no network request",
            "no security certification",
            "no legal or tax certification",
            "no guaranteed commercial outcome",
        ],
    }
    receipt = OAKGateRunReceipt(
        run_id=run_id,
        repository_id=report.repository_id,
        authorization_id=report.authorization_id,
        report_hash=report.report_hash,
        manifest_hash=manifest.manifest_hash,
        merkle_root=manifest.merkle_root,
        files_in_bundle=len(manifest.entries),
        external_actions=tuple(body["external_actions"]),
        non_claims=tuple(body["non_claims"]),
        receipt_hash=digest_payload(body),
    )
    receipt_path = destination / "run-receipt.json"
    receipt_path.write_text(
        json.dumps(
            receipt.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return report, receipt
