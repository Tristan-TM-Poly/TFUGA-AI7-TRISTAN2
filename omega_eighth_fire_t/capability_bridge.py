from __future__ import annotations

from dataclasses import dataclass

from omega_capability_os_t.core import Capability, stable_digest


@dataclass(frozen=True)
class FirePacket:
    capability_id: str
    domains: tuple[str, ...]
    consumes: tuple[str, ...]
    produces: tuple[str, ...]
    authority: str
    source_kind: str
    evidence_status: str
    fingerprint: str
    oak_boundary: str = (
        "A Capability OS declaration is a routable capability contract, not proof that the capability "
        "was executed successfully or that beneficiary capability increased."
    )


def capability_to_fire_packet(capability: Capability) -> FirePacket:
    payload = {
        "capability_id": capability.capability_id,
        "domains": capability.domains,
        "consumes": capability.consumes,
        "produces": capability.produces,
        "authority": capability.authority,
        "source_kind": "capability_os_contract",
        "evidence_status": "DECLARED_NOT_MEASURED",
    }
    return FirePacket(**payload, fingerprint=stable_digest(payload))
