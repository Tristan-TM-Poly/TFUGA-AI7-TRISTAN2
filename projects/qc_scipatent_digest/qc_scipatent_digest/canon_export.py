from __future__ import annotations

from .models import DigestDocument, Opportunity


def document_card(doc: DigestDocument) -> dict:
    return {
        "type": "document",
        "id": doc.doc_id,
        "title": doc.title,
        "kind": doc.kind,
        "institution": doc.institution,
        "topics": doc.topics,
        "oak_status": "synthetic_fixture",
    }


def opportunity_card(opp: Opportunity) -> dict:
    return {
        "type": "opportunity",
        "id": opp.opportunity_id,
        "title": opp.title,
        "science_doc": opp.science_doc,
        "ip_doc": opp.ip_doc,
        "bridge_topics": opp.bridge_topics,
        "oak_status": opp.oak_status,
        "release_class": opp.release_class,
    }


def markdown_cards(cards: list[dict]) -> str:
    lines = ["# DCT++ Canon Cards", ""]
    for card in cards:
        lines.append(f"## {card['type']} — {card['id']}")
        for key, value in card.items():
            if key not in {"type", "id"}:
                lines.append(f"- {key}: {value}")
        lines.append("")
    return "\n".join(lines)
