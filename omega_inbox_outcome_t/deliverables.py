"""Deterministic, file-backed deliverable factory."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import CaseRecord, DeliverableManifest, Intent
from .security import sha256_value


def _write_text(path: Path, content: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "media_type": "text/markdown", "sha256": sha256_value(content), "size_bytes": len(content.encode("utf-8"))}


def _write_json(path: Path, payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "media_type": "application/json", "sha256": sha256_value(payload), "size_bytes": len(text.encode("utf-8"))}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row}) if rows else ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows or [{"status": "no_rows"}])
    content = path.read_text(encoding="utf-8")
    return {"path": str(path), "media_type": "text/csv", "sha256": sha256_value(content), "size_bytes": len(content.encode("utf-8"))}


def _acknowledgment(case: CaseRecord) -> str:
    return (
        f"Bonjour,\n\nVotre demande a été reçue et enregistrée sous le dossier {case.case_id}. "
        "Nous vérifions les informations, les autorisations et les livrables requis avant toute transmission.\n\n"
        f"Référence : {case.case_id}\n"
    )


def _report(case: CaseRecord) -> str:
    return (
        f"# Rapport préparatoire — {case.case_id}\n\n"
        f"## Demande\n{case.analysis.explicit_requests[0] if case.analysis.explicit_requests else 'Non spécifiée'}\n\n"
        "## Statut épistémique\nCe rapport est un brouillon généré. Toute affirmation finale doit être reliée à une source, "
        "un test ou une preuve vérifiée.\n\n"
        "## Contrôles requis\n- provenance des données;\n- reproductibilité;\n- confidentialité;\n- propriété intellectuelle;\n- destinataire autorisé.\n"
    )


def _proposal(case: CaseRecord) -> str:
    return (
        f"# Proposition préparatoire — {case.case_id}\n\n"
        "## Besoin compris\nÀ confirmer avec le demandeur.\n\n"
        "## Portée candidate\n- découverte;\n- prototype;\n- validation OAK;\n- livraison et transfert.\n\n"
        "## Conditions\nAucun prix, échéancier, engagement ou responsabilité n'est accepté sans approbation humaine.\n"
    )


def build_deliverable(case: CaseRecord, workspace: Path) -> DeliverableManifest:
    root = workspace / case.case_id
    intent = case.analysis.primary_intent
    outputs: list[dict[str, Any]] = []
    deliverable_type = "reply_packet"

    if intent in {Intent.STATUS_REQUEST, Intent.SUPPORT_QUESTION, Intent.ACKNOWLEDGMENT}:
        deliverable_type = "verified_reply_draft"
        outputs.append(_write_text(root / "reply.md", _acknowledgment(case)))
    elif intent is Intent.TECHNICAL_REPORT:
        deliverable_type = "technical_report_draft"
        outputs.append(_write_text(root / "report.md", _report(case)))
        outputs.append(_write_csv(root / "metrics.csv", [{"metric": "placeholder", "value": "requires_verified_source"}]))
    elif intent is Intent.BUG_REPORT:
        deliverable_type = "bug_triage_packet"
        issue = {
            "title": case.analysis.explicit_requests[0] if case.analysis.explicit_requests else "Bug report",
            "body": "Reproduction and failing test are required before any patch claim.",
            "labels": ["bug", "oak-triage"],
            "case_id": case.case_id,
        }
        outputs.append(_write_json(root / "github_issue.json", issue))
        outputs.append(_write_text(root / "reply.md", _acknowledgment(case)))
    elif intent in {Intent.PROPOSAL_REQUEST, Intent.QUOTE_REQUEST}:
        deliverable_type = "commercial_proposal_draft"
        outputs.append(_write_text(root / "proposal.md", _proposal(case)))
    elif intent is Intent.INVOICE_REQUEST:
        deliverable_type = "invoice_draft"
        outputs.append(_write_json(root / "invoice.json", {"case_id": case.case_id, "status": "DRAFT", "amount": None, "contract_verified": False}))
    elif intent in {Intent.CONTRACT_OR_LEGAL, Intent.GOVERNMENT_OR_TAX, Intent.PRIVACY_REQUEST, Intent.SECURITY_INCIDENT, Intent.IP_OR_CONFIDENTIAL}:
        deliverable_type = "professional_review_packet"
        outputs.append(_write_json(root / "review_packet.json", {"case": case.to_dict(), "status": "PROFESSIONAL_REVIEW_REQUIRED"}))
    else:
        deliverable_type = "clarification_request"
        outputs.append(_write_text(root / "clarification.md", _acknowledgment(case) + "\nDes précisions sont nécessaires avant de poursuivre.\n"))

    manifest = DeliverableManifest(
        deliverable_id=f"DEL-{case.case_id}",
        case_id=case.case_id,
        deliverable_type=deliverable_type,
        version="0.1.0",
        company_id=case.company_id,
        division_id=case.division_id,
        input_refs=[{"event_id": case.event_id, "analysis_confidence": case.analysis.confidence}],
        outputs=outputs,
        data_class=case.analysis.requested_data_class,
        claims=[],
    )
    manifest.status = "GENERATED"
    _write_json(root / "manifest.json", manifest.to_dict())
    return manifest
