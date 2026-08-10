from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Mapping


_ALLOWED_ACCESS = {"public", "consented", "synthetic"}


@dataclass(frozen=True)
class DatasetManifest:
    """Minimal provenance contract for a neuroscience dataset payload.

    The manifest records what was used, where it came from, how it may be
    accessed, and the exact bytes observed by the benchmark. It does not
    certify the scientific quality of the source.
    """

    dataset_id: str
    version: str
    source_uri: str
    license_id: str
    access_mode: str
    sha256: str
    citation: str = ""

    def __post_init__(self) -> None:
        for name in ("dataset_id", "version", "source_uri", "license_id"):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if self.access_mode not in _ALLOWED_ACCESS:
            raise ValueError(f"access_mode must be one of {sorted(_ALLOWED_ACCESS)}")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256.lower()):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")

    def to_dict(self) -> Mapping[str, str]:
        return asdict(self)


def sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def build_manifest(
    payload: bytes,
    *,
    dataset_id: str,
    version: str,
    source_uri: str,
    license_id: str,
    access_mode: str,
    citation: str = "",
) -> DatasetManifest:
    return DatasetManifest(
        dataset_id=dataset_id,
        version=version,
        source_uri=source_uri,
        license_id=license_id,
        access_mode=access_mode,
        sha256=sha256_bytes(payload),
        citation=citation,
    )


def verify_payload(manifest: DatasetManifest, payload: bytes) -> bool:
    return sha256_bytes(payload) == manifest.sha256
