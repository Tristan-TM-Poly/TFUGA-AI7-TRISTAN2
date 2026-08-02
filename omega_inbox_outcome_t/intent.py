"""Deterministic intent and requirement extraction baseline."""
from __future__ import annotations

import re

from .models import DataClass, IntakeEvent, Intent, RequestAnalysis

RULES: tuple[tuple[Intent, tuple[str, ...]], ...] = (
    (Intent.SECURITY_INCIDENT, ("security incident", "incident de sécurité", "vulnerability", "vulnérabilité", "breach", "compromis")),
    (Intent.PRIVACY_REQUEST, ("delete my data", "supprimer mes données", "access request", "demande d'accès", "personal information")),
    (Intent.PAYMENT_CHANGE, ("bank account", "coordonnées bancaires", "wire", "virement", "change payment")),
    (Intent.GOVERNMENT_OR_TAX, ("government", "gouvernement", "tax", "impôt", "neq", "cra", "revenu québec")),
    (Intent.CONTRACT_OR_LEGAL, ("contract", "contrat", "nda", "legal", "juridique", "liability", "responsabilité")),
    (Intent.IP_OR_CONFIDENTIAL, ("patent", "brevet", "trade secret", "secret commercial", "confidential", "confidentiel", "source code")),
    (Intent.INVOICE_REQUEST, ("invoice", "facture", "billing", "reçu")),
    (Intent.QUOTE_REQUEST, ("quote", "devis", "price", "prix", "estimate", "estimation")),
    (Intent.PROPOSAL_REQUEST, ("proposal", "proposition", "statement of work", "appel d'offres")),
    (Intent.BUG_REPORT, ("bug", "bogue", "error", "erreur", "crash", "does not work", "ne fonctionne pas")),
    (Intent.FEATURE_REQUEST, ("feature request", "fonctionnalité", "could you add", "ajouter une fonction")),
    (Intent.TECHNICAL_REPORT, ("technical report", "rapport technique", "benchmark", "analyse de performance")),
    (Intent.DOCUMENT_REQUEST, ("document", "documentation", "manual", "manuel", "send me", "envoyez-moi")),
    (Intent.STATUS_REQUEST, ("status", "statut", "update", "mise à jour", "where are we", "où en sommes")),
    (Intent.SUPPORT_QUESTION, ("how do i", "comment faire", "help", "aide", "question", "support")),
)

FORMAT_WORDS = ("pdf", "csv", "json", "xlsx", "spreadsheet", "tableur", "presentation", "présentation", "github", "zip")
DEADLINE_PATTERN = re.compile(r"\b(?:before|avant|by|d'ici|deadline)\s+([^\n,.!?]+)", re.IGNORECASE)


def _term_matches(text: str, term: str) -> bool:
    if len(term) <= 4 and term.replace(" ", "").isalnum():
        return re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text) is not None
    return term in text


def analyze_request(event: IntakeEvent) -> RequestAnalysis:
    text = f"{event.subject}\n{event.body}".lower()
    matches: list[Intent] = []
    for intent, terms in RULES:
        if any(_term_matches(text, term) for term in terms):
            matches.append(intent)

    primary = matches[0] if matches else Intent.UNKNOWN
    formats = [word for word in FORMAT_WORDS if word in text]
    deadline_match = DEADLINE_PATTERN.search(text)
    ambiguities: list[str] = []
    if primary is Intent.UNKNOWN:
        ambiguities.append("intent_not_resolved")
    if any(word in text for word in ("latest", "dernier", "récente", "recent")) and not event.attachments:
        ambiguities.append("referenced_latest_artifact_not_identified")

    commercial = primary in {Intent.PROPOSAL_REQUEST, Intent.QUOTE_REQUEST}
    requested_class = DataClass.PUBLIC
    if any(word in text for word in ("confidential", "confidentiel", "private", "privé")):
        requested_class = DataClass.CLIENT_CONFIDENTIAL
    if any(word in text for word in ("personal information", "renseignement personnel", "identity document")):
        requested_class = DataClass.PERSONAL
    if any(word in text for word in ("secret", "credential", "mot de passe", "private key")):
        requested_class = DataClass.SECRET

    confidence = 0.35 if primary is Intent.UNKNOWN else min(0.98, 0.68 + 0.06 * len(matches))
    explicit = [event.subject.strip()] if event.subject.strip() else []
    implicit = [
        "verify_recipient_authority",
        "preserve_source_provenance",
        "run_security_privacy_ip_gates",
        "bind_delivery_to_output_hashes",
    ]
    if event.attachments:
        implicit.extend(("scan_attachments", "validate_attachment_provenance"))

    return RequestAnalysis(
        primary_intent=primary,
        secondary_intents=matches[1:],
        explicit_requests=explicit,
        implicit_requirements=implicit,
        ambiguities=ambiguities,
        requested_formats=formats,
        deadline_text=deadline_match.group(1).strip() if deadline_match else None,
        commercial=commercial,
        requested_data_class=requested_class,
        confidence=confidence,
    )
