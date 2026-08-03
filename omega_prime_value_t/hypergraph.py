from __future__ import annotations

from typing import Any

from .models import PrimeCandidate, PrimeCertificate


def build_prime_hypergraph(
    candidates: list[PrimeCandidate], certificates: list[PrimeCertificate]
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {"id": "family:proth", "type": "family", "label": "Proth"},
        {"id": "application:ntt", "type": "application", "label": "NTT"},
        {"id": "proof:proth", "type": "proof_method", "label": "Proth theorem"},
    ]
    hyperedges: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = f"candidate:{candidate.value}"
        nodes.append(
            {
                "id": candidate_id,
                "type": "prime_candidate",
                "value": str(candidate.value),
                "status": candidate.status.value,
                "parameters": candidate.parameters,
            }
        )
        hyperedges.append(
            {
                "id": f"edge:family:{candidate.value}",
                "type": "belongs_to_family",
                "members": [candidate_id, "family:proth"],
            }
        )
        if candidate.small_factor:
            factor_id = f"factor:{candidate.small_factor}"
            nodes.append({"id": factor_id, "type": "factor", "value": candidate.small_factor})
            hyperedges.append(
                {
                    "id": f"edge:factor:{candidate.value}",
                    "type": "certifies_compositeness",
                    "members": [candidate_id, factor_id],
                }
            )
    for certificate in certificates:
        value = int(certificate.candidate["value"])
        certificate_node = f"certificate:{certificate.certificate_id}"
        nodes.append(
            {
                "id": certificate_node,
                "type": "certificate",
                "sha256": certificate.sha256,
            }
        )
        hyperedges.append(
            {
                "id": f"edge:certifies:{value}",
                "type": "certifies",
                "members": [certificate_node, f"candidate:{value}", "proof:proth"],
            }
        )
        if certificate.verification.get("ntt_profile"):
            hyperedges.append(
                {
                    "id": f"edge:application:{value}",
                    "type": "supports_application",
                    "members": [f"candidate:{value}", "application:ntt"],
                }
            )
    unique_nodes = {node["id"]: node for node in nodes}
    return {
        "schema_version": "omega-prime-hg-v1",
        "nodes": [unique_nodes[key] for key in sorted(unique_nodes)],
        "hyperedges": sorted(hyperedges, key=lambda item: item["id"]),
        "claims": {
            "mathematical_novelty_claimed": False,
            "record_claimed": False,
            "commercial_exclusivity_claimed": False,
        },
    }
