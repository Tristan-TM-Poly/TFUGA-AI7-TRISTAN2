"""Distribution and VCS provenance discovery for runtime plugins."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import metadata
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class DistributionFingerprint:
    distribution: str = ""
    version: str = ""
    repository: str = ""
    commit: str = ""
    install_source: str = ""
    wheel_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fingerprint_distribution(distribution: str | None) -> DistributionFingerprint:
    if not distribution:
        return DistributionFingerprint()
    try:
        dist = metadata.distribution(distribution)
    except metadata.PackageNotFoundError:
        return DistributionFingerprint(distribution=distribution)
    repository = ""
    commit = ""
    install_source = ""
    try:
        direct = json.loads(dist.read_text("direct_url.json") or "{}")
    except (json.JSONDecodeError, OSError):
        direct = {}
    if direct:
        install_source = str(direct.get("url", ""))
        vcs = direct.get("vcs_info") or {}
        commit = str(vcs.get("commit_id", ""))
        repository = install_source.removeprefix("git+")
    return DistributionFingerprint(
        distribution=dist.metadata.get("Name", distribution),
        version=dist.version,
        repository=repository,
        commit=commit,
        install_source=install_source,
    )
