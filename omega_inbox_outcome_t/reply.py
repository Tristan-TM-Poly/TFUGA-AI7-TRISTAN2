"""Content-bound reply drafting for a validated case and route."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import CaseRecord, Channel, DeliverableManifest, GateResult, RoutingDecision, ValidationResult, ValidationStatus
from .security import sha256_value


@dataclass(frozen=True, slots=True)
class ReplyDraft:
    case_id: str
    to: str
    subject: str
    body: str
    channel: Channel
    deliverable_id: str
    deliverable_version: str
    output_hashes: dict[str, str]
    reply_hash: str
    send_authorized: bool
    authorization_reason: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["channel"] = self.channel.value
        return payload


def compose_reply(
    case: CaseRecord,
    manifest: DeliverableManifest,
    validation: ValidationResult,
    gate: GateResult,
    route: RoutingDecision,
    destination: str,
) -> ReplyDraft:
    hashes = {str(item["path"]): str(item["sha256"]) for item in manifest.outputs}
    if route.primary_channel is Channel.EMAIL:
        delivery_sentence = "Les livrables préparés sont associés à ce message de livraison."
    else:
        delivery_sentence = f"Les livrables doivent être déposés par le canal sécurisé `{route.primary_channel.value}`; ce courriel sert de notification."

    body = (
        f"Bonjour,\n\nVotre dossier {case.case_id} a été traité jusqu'au stade `{manifest.status}`. "
        f"Le paquet `{manifest.deliverable_id}` version {manifest.version} a été généré.\n\n"
        f"{delivery_sentence}\n\n"
        "Cette notification ne constitue ni une acceptation contractuelle ni une confirmation de réception finale.\n\n"
        f"Référence : {case.case_id}\n"
    )
    payload = {
        "case_id": case.case_id,
        "to": destination,
        "subject": f"[{case.case_id}] Livraison préparée",
        "body": body,
        "channel": route.primary_channel.value,
        "deliverable_id": manifest.deliverable_id,
        "deliverable_version": manifest.version,
        "output_hashes": hashes,
    }
    auto_gate = gate.decision.value in {"AUTO_REPLY", "AUTO_BOUNDED_DISPATCH"}
    send_authorized = auto_gate and validation.status is ValidationStatus.PASS
    reason = "bounded_policy_and_oak_pass" if send_authorized else "draft_only_requires_dispatch_gate_or_approval"
    return ReplyDraft(
        case_id=case.case_id,
        to=destination,
        subject=payload["subject"],
        body=body,
        channel=route.primary_channel,
        deliverable_id=manifest.deliverable_id,
        deliverable_version=manifest.version,
        output_hashes=hashes,
        reply_hash=sha256_value(payload),
        send_authorized=send_authorized,
        authorization_reason=reason,
    )
