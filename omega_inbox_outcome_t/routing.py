"""Channel selection and dry-run dispatch adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .models import Channel, DataClass, DeliverableManifest, DeliveryReceipt, ResolvedIdentity, RoutingDecision
from .security import sha256_value


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    email_attachment_limit_bytes: int = 5_000_000
    confidential_channels: tuple[Channel, ...] = (Channel.DRIVE, Channel.DROPBOX, Channel.PORTAL, Channel.SFTP)
    source_code_channels: tuple[Channel, ...] = (Channel.GITHUB, Channel.PORTAL)


def choose_route(
    manifest: DeliverableManifest,
    identity: ResolvedIdentity,
    destination: str,
    *,
    policy: RoutingPolicy = RoutingPolicy(),
) -> RoutingDecision:
    total_size = sum(int(output.get("size_bytes", 0)) for output in manifest.outputs)
    media = {str(output.get("media_type")) for output in manifest.outputs}
    reasons: list[str] = []

    if any("github" in str(output.get("path", "")) for output in manifest.outputs) and identity.may_receive_source_code:
        primary = Channel.GITHUB
        reasons.append("code_or_issue_delivery")
    elif manifest.data_class in {DataClass.CLIENT_CONFIDENTIAL, DataClass.PERSONAL, DataClass.RESTRICTED, DataClass.SECRET}:
        primary = Channel.PORTAL
        reasons.append("sensitive_class_requires_access_control")
    elif total_size > policy.email_attachment_limit_bytes:
        primary = Channel.DRIVE
        reasons.append("package_exceeds_email_limit")
    elif "application/json" in media and manifest.deliverable_type.endswith("packet"):
        primary = Channel.PORTAL
        reasons.append("structured_case_packet")
    else:
        primary = Channel.EMAIL
        reasons.append("small_low_risk_delivery")

    notification = None if primary is Channel.EMAIL else Channel.EMAIL
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat() if primary in {Channel.DRIVE, Channel.DROPBOX, Channel.PORTAL, Channel.SFTP} else None
    return RoutingDecision(manifest.deliverable_id, primary, notification, destination, tuple(reasons), expiry, False)


class DryRunDispatcher:
    """Records an intended transmission without network effects."""

    def dispatch(self, case_id: str, manifest: DeliverableManifest, route: RoutingDecision) -> DeliveryReceipt:
        hashes = {str(output["path"]): str(output["sha256"]) for output in manifest.outputs}
        return DeliveryReceipt(
            receipt_id=f"RECEIPT-{sha256_value({'case': case_id, 'deliverable': manifest.deliverable_id, 'route': route.primary_channel.value})[:16]}",
            case_id=case_id,
            deliverable_id=manifest.deliverable_id,
            channel=route.primary_channel,
            destination=route.destination,
            content_hashes=hashes,
            status="DRY_RUN_PREPARED",
            metadata={"notification_channel": route.notification_channel.value if route.notification_channel else None, "reasons": list(route.reasons)},
        )
