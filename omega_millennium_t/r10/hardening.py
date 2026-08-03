"""Cross-cutting hardening for the R0.10 streaming layer."""
from __future__ import annotations

from typing import Any

from . import audit as _audit_module
from . import compiler as _compiler_module
from .model import stable_digest
from .store import AtlasStore

_BASE_MANIFEST = _compiler_module._manifest


def _manifest_with_compatibility(store: AtlasStore, state: dict[str, Any]) -> dict[str, Any]:
    manifest = _BASE_MANIFEST(store, state)
    compatibility = store.get_metadata("source_compatibility")
    if compatibility is not None:
        manifest.pop("manifest_digest", None)
        manifest["source_compatibility"] = compatibility
        manifest["manifest_digest"] = stable_digest(manifest)
    return manifest


def install_hardening() -> None:
    if getattr(AtlasStore, "_r10_hardening_installed", False):
        return
    AtlasStore._r10_hardening_installed = True
    _compiler_module._manifest = _manifest_with_compatibility
    _audit_module._manifest = _manifest_with_compatibility
