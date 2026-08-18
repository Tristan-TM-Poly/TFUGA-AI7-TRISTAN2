from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Iterable

from .world import ATTACHMENT_PROTOCOL


PUBLICATION_PROTOCOL = "OMEGA-PUBLICATION-FABRIC/0.1"
RIGHTS_MODES = {"owned", "licensed", "semantic_original"}


class PublicationSpecError(ValueError):
    """Raised when a publication bundle would violate the cross-surface contract."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PublicationSpecError(f"{path} must be a non-empty string")
    return value.strip()


def _string_list(values: Iterable[str] | None, path: str) -> list[str]:
    if values is None:
        return []
    out: list[str] = []
    for index, value in enumerate(values):
        text = _text(value, f"{path}[{index}]")
        if text not in out:
            out.append(text)
    return out


def validate_publication_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    root = deepcopy(bundle)
    if root.get("protocol") != PUBLICATION_PROTOCOL:
        raise PublicationSpecError(f"protocol must be {PUBLICATION_PROTOCOL}")

    source = root.get("source")
    if not isinstance(source, dict):
        raise PublicationSpecError("source must be an object")
    _text(source.get("capsule_id"), "source.capsule_id")
    world_sha = _text(source.get("world_sha256"), "source.world_sha256")
    if len(world_sha) != 64:
        raise PublicationSpecError("source.world_sha256 must be a SHA-256 hex digest")
    scientific_status = _text(source.get("scientific_status"), "source.scientific_status")

    narrative = root.get("narrative")
    if not isinstance(narrative, dict):
        raise PublicationSpecError("narrative must be an object")
    _text(narrative.get("title"), "narrative.title")
    _text(narrative.get("summary"), "narrative.summary")

    rights = root.get("rights")
    if not isinstance(rights, dict):
        raise PublicationSpecError("rights must be an object")
    mode = _text(rights.get("mode"), "rights.mode")
    if mode not in RIGHTS_MODES:
        raise PublicationSpecError(f"unsupported rights mode: {mode}")
    if rights.get("reuse_distinctive_third_party_assets") is not False:
        raise PublicationSpecError("distinctive third-party assets must never be reused by this contract")

    surfaces = root.get("surfaces")
    if not isinstance(surfaces, dict):
        raise PublicationSpecError("surfaces must be an object")
    for surface in ("web", "github", "youtube"):
        if not isinstance(surfaces.get(surface), dict):
            raise PublicationSpecError(f"surfaces.{surface} must be an object")

    youtube = surfaces["youtube"]
    if not isinstance(youtube.get("publication_authorized"), bool):
        raise PublicationSpecError("surfaces.youtube.publication_authorized must be boolean")
    expected_mode = "publish_candidate" if youtube["publication_authorized"] else "draft_export_only"
    if youtube.get("mode") != expected_mode:
        raise PublicationSpecError(f"surfaces.youtube.mode must be {expected_mode}")
    if youtube["publication_authorized"] and not youtube.get("channels"):
        raise PublicationSpecError("authorized YouTube publication requires at least one declared channel")

    oak = root.get("oak")
    if not isinstance(oak, dict):
        raise PublicationSpecError("oak must be an object")
    if oak.get("scientific_status") != scientific_status:
        raise PublicationSpecError("publication must preserve the source scientific status")
    required_false = (
        "simulation_is_proof",
        "visualization_is_truth",
        "popularity_is_evidence",
        "publication_is_validation",
    )
    for field in required_false:
        if oak.get(field) is not False:
            raise PublicationSpecError(f"oak.{field} must be false")
    if oak.get("external_publication_requires_explicit_authority") is not True:
        raise PublicationSpecError("external publication must remain explicitly authorized")

    return root


def compile_publication_bundle(
    sim_capsule: dict[str, Any],
    *,
    title: str,
    summary: str,
    claim_ids: Iterable[str] | None = None,
    evidence_refs: Iterable[str] | None = None,
    website_path: str | None = None,
    github_repo: str | None = None,
    youtube_channels: Iterable[str] | None = None,
    rights_mode: str = "semantic_original",
    publication_authorized: bool = False,
) -> dict[str, Any]:
    """Compile one SimCapsule into a portable Web/GitHub/YouTube publication contract.

    This is deliberately a planning/export ABI, not a publishing client. In particular,
    YouTube remains ``draft_export_only`` unless explicit publication authority is passed,
    and even then the result is only a publish candidate: no external API call occurs here.
    """

    if not isinstance(sim_capsule, dict) or sim_capsule.get("protocol") != ATTACHMENT_PROTOCOL:
        raise PublicationSpecError(f"sim_capsule.protocol must be {ATTACHMENT_PROTOCOL}")

    capsule_id = _text(sim_capsule.get("capsule_id"), "sim_capsule.capsule_id")
    world_sha256 = _text(sim_capsule.get("world_sha256"), "sim_capsule.world_sha256")
    oak = sim_capsule.get("oak")
    if not isinstance(oak, dict):
        raise PublicationSpecError("sim_capsule.oak must be an object")
    scientific_status = _text(oak.get("scientific_status"), "sim_capsule.oak.scientific_status")

    if rights_mode not in RIGHTS_MODES:
        raise PublicationSpecError(f"unsupported rights mode: {rights_mode}")

    channels = _string_list(youtube_channels, "youtube_channels")
    claims = _string_list(claim_ids, "claim_ids")
    evidence = _string_list(evidence_refs, "evidence_refs")
    web_route = website_path.strip() if isinstance(website_path, str) and website_path.strip() else None
    repo = github_repo.strip() if isinstance(github_repo, str) and github_repo.strip() else None

    youtube_mode = "publish_candidate" if publication_authorized else "draft_export_only"
    bundle_core = {
        "protocol": PUBLICATION_PROTOCOL,
        "source": {
            "kind": "SimCapsule",
            "protocol": ATTACHMENT_PROTOCOL,
            "capsule_id": capsule_id,
            "world_sha256": world_sha256,
            "scientific_status": scientific_status,
        },
        "narrative": {
            "title": _text(title, "title"),
            "summary": _text(summary, "summary"),
            "claim_ids": claims,
            "evidence_refs": evidence,
        },
        "surfaces": {
            "web": {
                "enabled": web_route is not None,
                "route": web_route,
                "attachment_slot": "SimSlot",
                "interaction": ["inspect", "fork", "compare", "reset", "show_evidence", "show_falsifier"],
            },
            "github": {
                "enabled": repo is not None,
                "repository": repo,
                "artifacts": ["sim-capsule.json", "publication-bundle.json"],
            },
            "youtube": {
                "enabled": bool(channels),
                "channels": channels,
                "publication_authorized": bool(publication_authorized),
                "mode": youtube_mode,
                "renditions": [
                    {"id": "silent_master", "audio": False, "purpose": "scientific_visual_master"},
                    {"id": "longform", "audio": True, "purpose": "explanation"},
                    {"id": "short", "audio": True, "purpose": "verified_discovery_unit"},
                ],
            },
        },
        "rights": {
            "mode": rights_mode,
            "reuse_distinctive_third_party_assets": False,
            "semantic_original_required": rights_mode == "semantic_original",
        },
        "provenance": {
            "content_addressed": True,
            "generated_from_sim_capsule": True,
            "source_world_sha256": world_sha256,
        },
        "oak": {
            "scientific_status": scientific_status,
            "simulation_is_proof": False,
            "visualization_is_truth": False,
            "popularity_is_evidence": False,
            "publication_is_validation": False,
            "external_publication_requires_explicit_authority": True,
            "residues": list(oak.get("residues", [])),
        },
    }
    bundle = deepcopy(bundle_core)
    bundle["bundle_sha256"] = _sha256(bundle_core)
    bundle["bundle_id"] = f"publication@{bundle['bundle_sha256'][:16]}"
    return validate_publication_bundle(bundle)
