from __future__ import annotations

from hashlib import sha256
import mimetypes
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import ProofArtifact, ValidationReceipt, stable_digest


class ProofArtifactBuilder:
    def build(
        self,
        path: str | Path,
        *,
        root: str | Path | None = None,
        provenance: Iterable[str],
        derived_from: Iterable[str] = (),
        validations: Iterable[ValidationReceipt] = (),
        epistemic_status: str = "PROTOTYPED",
        uncertainty: Mapping[str, Any] | None = None,
        risks: Iterable[str] = (),
        publication_authorized: bool = False,
    ) -> ProofArtifact:
        file_path = Path(path)
        content = file_path.read_bytes()
        digest = sha256(content).hexdigest()
        display_path = file_path.resolve()
        if root is not None:
            display_path = file_path.resolve().relative_to(Path(root).resolve())
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        provenance_tuple = tuple(dict.fromkeys(str(item) for item in provenance if str(item)))
        if not provenance_tuple:
            raise ValueError("proof artifact requires provenance")
        derived = tuple(dict.fromkeys(str(item) for item in derived_from if str(item)))
        receipts = tuple(validations)
        identity = {
            "path": display_path.as_posix(),
            "sha256": digest,
            "provenance": provenance_tuple,
            "derived_from": derived,
        }
        return ProofArtifact(
            artifact_id=f"ART-{stable_digest(identity)[:20].upper()}",
            path=display_path.as_posix(),
            sha256=digest,
            size_bytes=len(content),
            media_type=media_type,
            provenance=provenance_tuple,
            derived_from=derived,
            validations=receipts,
            epistemic_status=epistemic_status,
            uncertainty=dict(uncertainty or {}),
            risks=tuple(dict.fromkeys(str(item) for item in risks if str(item))),
            publication_authorized=publication_authorized,
        )

    @staticmethod
    def verify(artifact: ProofArtifact, path: str | Path) -> dict[str, Any]:
        content = Path(path).read_bytes()
        actual = sha256(content).hexdigest()
        return {
            "artifact_id": artifact.artifact_id,
            "passed": actual == artifact.sha256 and len(content) == artifact.size_bytes,
            "expected_sha256": artifact.sha256,
            "actual_sha256": actual,
            "expected_size_bytes": artifact.size_bytes,
            "actual_size_bytes": len(content),
        }
