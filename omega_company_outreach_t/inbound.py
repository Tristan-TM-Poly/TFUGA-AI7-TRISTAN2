from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Mapping

from .models import MailEventType, PublicMailEvent, ReplyClass, hmac_sha256_text


_AUTO = re.compile(
    r"\b(auto(?:matic)? reply|out of office|absence|absent|congé|vacation|retour le)\b",
    re.IGNORECASE,
)
_BOUNCE = re.compile(
    r"\b(delivery status notification|undeliverable|mail delivery failed|adresse introuvable|rejected)\b",
    re.IGNORECASE,
)
_UNSUBSCRIBE = re.compile(
    r"\b(unsubscribe|désabonn|remove me|ne plus me contacter)\b",
    re.IGNORECASE,
)
_DECLINE = re.compile(
    r"\b(no interest|not interested|decline|refus|pas intéress|ne donnera pas suite|cannot participate)\b",
    re.IGNORECASE,
)
_REFERRAL = re.compile(
    r"\b(contact|contacter|refer|référ|diriger|redirect|bonne personne|right person)\b",
    re.IGNORECASE,
)
_INFORMATION = re.compile(
    r"\b(send|provide|share|document|budget|proposal|information|renseignement|détails|detail|pièce)\b",
    re.IGNORECASE,
)
_POSITIVE = re.compile(
    r"\b(yes|oui|interested|intéress|meeting|rencontre|discuss|échanger|available|disponible)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class PrivateMailMetadata:
    case_id: str
    provider_message_id: str
    provider_thread_id: str
    counterparty: str
    occurred_at: str
    subject: str = ""
    snippet: str = ""
    headers: Mapping[str, str] | None = None
    source_issue: int | None = None


def classify_reply(subject: str, snippet: str, headers: Mapping[str, str] | None = None) -> ReplyClass:
    combined = f"{subject}\n{snippet}"
    headers = {str(k).casefold(): str(v) for k, v in (headers or {}).items()}
    auto_header = headers.get("auto-submitted", "").casefold()
    precedence = headers.get("precedence", "").casefold()
    if auto_header not in {"", "no"} or precedence in {"bulk", "junk", "list"} or _AUTO.search(combined):
        return ReplyClass.AUTO_REPLY
    if _BOUNCE.search(combined):
        return ReplyClass.BOUNCE
    if _UNSUBSCRIBE.search(combined):
        return ReplyClass.UNSUBSCRIBE
    if _DECLINE.search(combined):
        return ReplyClass.DECLINE
    if _REFERRAL.search(combined):
        return ReplyClass.REFERRAL
    if _INFORMATION.search(combined):
        return ReplyClass.INFORMATION_REQUEST
    if _POSITIVE.search(combined):
        return ReplyClass.POSITIVE
    return ReplyClass.UNKNOWN


def build_public_event(
    metadata: PrivateMailMetadata,
    *,
    secret: str,
    event_id: str,
) -> PublicMailEvent:
    reply_class = classify_reply(metadata.subject, metadata.snippet, metadata.headers)
    event_type = {
        ReplyClass.AUTO_REPLY: MailEventType.AUTO_REPLY,
        ReplyClass.BOUNCE: MailEventType.BOUNCE,
        ReplyClass.UNSUBSCRIBE: MailEventType.UNSUBSCRIBE,
    }.get(reply_class, MailEventType.REPLY)
    occurred_at = metadata.occurred_at or datetime.now(timezone.utc).isoformat()
    event = PublicMailEvent(
        event_id=event_id,
        case_id=metadata.case_id,
        event_type=event_type,
        message_hash=hmac_sha256_text(metadata.provider_message_id, secret),
        thread_hash=hmac_sha256_text(metadata.provider_thread_id, secret),
        counterparty_hash=hmac_sha256_text(metadata.counterparty.casefold().strip(), secret),
        occurred_at=occurred_at,
        reply_class=reply_class,
        source_issue=metadata.source_issue,
        raw_content_retained=False,
    )
    errors = event.validate()
    if errors:
        raise ValueError("; ".join(errors))
    return event
