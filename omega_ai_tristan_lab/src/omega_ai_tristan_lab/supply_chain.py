"""Offline-first software supply-chain inventory and OAK checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib import metadata
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class PackageRecord:
    name: str
    version: str
    license: str
    requires: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SupplyChainReport:
    packages: tuple[PackageRecord, ...]
    wheel_hashes_verified: bool | None
    hash_errors: tuple[str, ...]
    vulnerability_status: str = "NOT_SCANNED_NO_VULNERABILITY_DB"

    @property
    def ok(self) -> bool:
        return self.wheel_hashes_verified is not False and not self.hash_errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "packages": [item.to_dict() for item in self.packages],
            "wheel_hashes_verified": self.wheel_hashes_verified,
            "hash_errors": list(self.hash_errors),
            "vulnerability_status": self.vulnerability_status,
            "ok": self.ok,
        }


class SupplyChainOAK:
    def inventory(self, distributions: Iterable[str]) -> tuple[PackageRecord, ...]:
        rows: list[PackageRecord] = []
        seen: set[str] = set()
        for requested in distributions:
            key = requested.lower().replace("_", "-")
            if key in seen:
                continue
            seen.add(key)
            try:
                dist = metadata.distribution(requested)
            except metadata.PackageNotFoundError:
                continue
            license_value = str(dist.metadata.get("License") or dist.metadata.get("License-Expression") or "UNKNOWN")
            rows.append(
                PackageRecord(
                    name=str(dist.metadata.get("Name") or requested),
                    version=dist.version,
                    license=license_value,
                    requires=tuple(dist.requires or ()),
                )
            )
        return tuple(sorted(rows, key=lambda item: item.name.lower()))

    def verify_wheelhouse(self, directory: str | Path, manifest: str | Path) -> tuple[bool, tuple[str, ...]]:
        root = Path(directory)
        rows = json.loads(Path(manifest).read_text(encoding="utf-8"))
        errors: list[str] = []
        for row in rows:
            path = root / row["file"]
            if not path.is_file():
                errors.append(f"missing wheel: {row['file']}")
                continue
            digest = sha256(path.read_bytes()).hexdigest()
            if digest != row["sha256"]:
                errors.append(f"hash mismatch: {row['file']}")
        return not errors, tuple(errors)

    def report(
        self,
        distributions: Iterable[str],
        *,
        wheelhouse: str | Path | None = None,
        hash_manifest: str | Path | None = None,
    ) -> SupplyChainReport:
        verified: bool | None = None
        errors: tuple[str, ...] = ()
        if wheelhouse is not None or hash_manifest is not None:
            if wheelhouse is None or hash_manifest is None:
                raise ValueError("wheelhouse and hash_manifest must be supplied together")
            verified, errors = self.verify_wheelhouse(wheelhouse, hash_manifest)
        return SupplyChainReport(self.inventory(distributions), verified, errors)
