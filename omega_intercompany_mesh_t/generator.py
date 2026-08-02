from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from .models import AgreementFamily, AgreementPacket, CompanyNode, LegalStatus, MailPacket


def default_nodes() -> list[CompanyNode]:
    return [
        CompanyNode("tristan_parent", "Tristan Parent OpCo", LegalStatus.CANDIDATE_ENTITY, "governance and shared control", "parent@company.test"),
        CompanyNode("tristan_oak", "Tristan OAK Systems", LegalStatus.INTERNAL_DIVISION, "verification, audit and risk", "oak@company.test"),
        CompanyNode("tristan_software", "Tristan Software Labs", LegalStatus.INTERNAL_DIVISION, "software delivery and automation", "software@company.test"),
        CompanyNode("tristan_research", "Tristan Research Foundry", LegalStatus.INTERNAL_DIVISION, "research, experiments and IP candidates", "research@company.test"),
    ]


CLAUSES = {
    AgreementFamily.OPERATING_CHARTER: [
        "Defines mission, authority, reporting and escalation boundaries.",
        "Does not create a separate legal person when the destination is an internal division.",
        "All irreversible legal or financial acts remain founder-controlled.",
    ],
    AgreementFamily.SHARED_SERVICES: [
        "Parent prepares shared administration, tooling and records.",
        "Costs are tracked internally and are not treated as third-party invoices without separate legal entities.",
        "Service levels and exceptions are recorded in the evidence ledger.",
    ],
    AgreementFamily.IP_LICENSE: [
        "No ownership transfer occurs through this draft.",
        "IP provenance, contributors and publication status must be verified.",
        "Any assignment or exclusive licence requires human signature and professional review.",
    ],
    AgreementFamily.DATA_PRIVACY: [
        "Use only necessary data for defined purposes.",
        "Respect recipient authority, retention and deletion policies.",
        "Sensitive or cross-border transfers require the applicable privacy gate.",
    ],
    AgreementFamily.DELIVERY_SLA: [
        "Every deliverable has a manifest, version, hashes and acceptance criteria.",
        "Provider acceptance is not recipient acceptance.",
        "Failed validation regenerates the deliverable rather than silently shipping it.",
    ],
    AgreementFamily.INVOICING: [
        "Internal divisions use cost allocation records, not legal intercompany invoices.",
        "Separate entities may invoice only after verified legal and tax configuration.",
        "Payments are never auto-executed by this packet.",
    ],
    AgreementFamily.SECURITY_COOPERATION: [
        "Security incidents may trigger immediate containment but not unauthorized disclosure.",
        "Credentials and private keys never travel by ordinary email.",
        "Critical incidents require founder escalation and preserved evidence.",
    ],
}


def generate_mesh(nodes: list[CompanyNode] | None = None) -> tuple[list[AgreementPacket], list[MailPacket]]:
    nodes = nodes or default_nodes()
    agreements: list[AgreementPacket] = []
    messages: list[MailPacket] = []
    counter = 1
    mail_counter = 1
    for source in nodes:
        for destination in nodes:
            if source.company_id == destination.company_id:
                continue
            thread_id = f"THR-{source.company_id}-{destination.company_id}"
            packet_ids: list[str] = []
            for family in AgreementFamily:
                packet = AgreementPacket(
                    packet_id=f"AGR-{counter:04d}",
                    source_company_id=source.company_id,
                    destination_company_id=destination.company_id,
                    family=family,
                    title=f"{family.value.replace('_', ' ').title()} — {source.display_name} → {destination.display_name}",
                    clauses=list(CLAUSES[family]),
                )
                packet.seal()
                agreements.append(packet)
                packet_ids.append(packet.packet_id)
                counter += 1

            messages.append(MailPacket(
                mail_id=f"MAIL-{mail_counter:04d}",
                thread_id=thread_id,
                source_company_id=source.company_id,
                destination_company_id=destination.company_id,
                stage="BOOTSTRAP_REQUEST",
                subject=f"[DRAFT/NON-BINDING] Bootstrap intercompany operating packet — {source.display_name} → {destination.display_name}",
                body=(
                    f"This synthetic internal message initializes the operating relationship from {source.display_name} "
                    f"to {destination.display_name}. The attached packet IDs are drafts only and create no legal obligation."
                ),
                agreement_packet_ids=tuple(packet_ids),
                external_send_allowed=False,
            ))
            mail_counter += 1
            messages.append(MailPacket(
                mail_id=f"MAIL-{mail_counter:04d}",
                thread_id=thread_id,
                source_company_id=destination.company_id,
                destination_company_id=source.company_id,
                stage="AUTO_ACKNOWLEDGMENT",
                subject=f"Re: [DRAFT/NON-BINDING] Bootstrap intercompany operating packet — {source.display_name} → {destination.display_name}",
                body=(
                    f"Automatic synthetic acknowledgment from {destination.display_name}. Packet received for OAK review; "
                    "no agreement is accepted, signed or activated by this acknowledgment."
                ),
                agreement_packet_ids=tuple(packet_ids),
                auto_reply=True,
                external_send_allowed=False,
            ))
            mail_counter += 1
    return agreements, messages


def write_mesh(output: Path) -> dict[str, int]:
    output.mkdir(parents=True, exist_ok=True)
    agreements, messages = generate_mesh()
    (output / "nodes.json").write_text(json.dumps([asdict(node) | {"legal_status": node.legal_status.value} for node in default_nodes()], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "agreements.jsonl").open("w", encoding="utf-8") as handle:
        for item in agreements:
            handle.write(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    with (output / "mail_packets.jsonl").open("w", encoding="utf-8") as handle:
        for item in messages:
            handle.write(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    manifest = {
        "nodes": len(default_nodes()),
        "directed_relationships": 12,
        "agreement_families": len(AgreementFamily),
        "agreement_packets": len(agreements),
        "mail_packets": len(messages),
        "real_external_sends": 0,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
