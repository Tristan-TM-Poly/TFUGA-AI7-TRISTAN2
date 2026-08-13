from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .contracts import MathArtifact


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_work_unit(*, work_unit_id: str, source_count: int, pilot: str = "proof-kernel-5") -> dict[str, Any]:
    """Emit the minimal Ω ecosystem WorkUnit envelope for this vertical slice."""

    return {
        "schema_version": "1.0",
        "work_unit_id": work_unit_id,
        "kind": "math_proof_research",
        "pilot": pilot,
        "source_count": source_count,
        "created_at": utc_now(),
        "claim_boundary": (
            "A WorkUnit records intent and execution scope; it is not proof that sources were fetched, "
            "claims are true, or formalizations are semantically faithful."
        ),
    }


def make_evidence_receipt(
    *, receipt_id: str, artifacts: list[MathArtifact], kernel_accepted: int = 0
) -> dict[str, Any]:
    """Create an OAK-safe receipt separating extraction from formal verification."""

    extracted = len(artifacts)
    oak_verified = sum(a.is_oak_verified() for a in artifacts)
    return {
        "schema_version": "1.0",
        "receipt_id": receipt_id,
        "kind": "math_proof_evidence_receipt",
        "created_at": utc_now(),
        "counts": {
            "source_extracted_artifacts": extracted,
            "kernel_accepted": kernel_accepted,
            "oak_verified": oak_verified,
        },
        "artifact_ids": [a.artifact_id for a in artifacts],
        "claim_boundary": (
            "Extracted != true; formalized != semantically faithful; kernel_accepted != empirical truth; "
            "redistributable must be established independently per source."
        ),
    }


def artifact_to_dict(artifact: MathArtifact) -> dict[str, Any]:
    return asdict(artifact)
