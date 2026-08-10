from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core import Capability, Intent, stable_digest
from .external import ExternalBinding
from .runtime import HandlerResult

CHATMEM_CAPABILITY_SCHEMA_VERSION = "0.4.0"

DEFAULT_REPOSITORY = "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2"
DEFAULT_BRANCH = "main"
DEFAULT_POINTER_PATH = "memory/chatgpt/CHATMEM_GLOBAL_POINTER.json"
DEFAULT_CONTEXT_PATH = "memory/chatgpt/live/2026-08-10T224200Z/canon/CHATGPT_CONTEXT_LIVE.md"
DEFAULT_LIBRARY_FOLDER = "/Tristan/ChatGPT Memory"


@dataclass(frozen=True)
class ChatMemCheckpointManifest:
    checkpoint_id: str
    previous_checkpoint: str
    oak_status: str
    public_derivation_only: bool
    raw_transcript_committed: bool
    source_hashes: tuple[str, ...]
    touched_systems: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ChatMemCheckpointManifest":
        return cls(
            checkpoint_id=str(payload.get("checkpoint_id", "")),
            previous_checkpoint=str(payload.get("previous_checkpoint", "")),
            oak_status=str(payload.get("oak_status", "")).upper(),
            public_derivation_only=bool(payload.get("public_derivation_only", False)),
            raw_transcript_committed=bool(payload.get("raw_transcript_committed", True)),
            source_hashes=tuple(map(str, payload.get("source_hashes", []))),
            touched_systems=tuple(map(str, payload.get("touched_systems", []))),
        )

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        if not self.checkpoint_id.strip():
            errors.append("checkpoint_id is required")
        if not self.previous_checkpoint.strip():
            errors.append("previous_checkpoint is required")
        if self.oak_status != "PASS":
            errors.append("oak_status must be PASS before persistence")
        if not self.public_derivation_only:
            errors.append("public_derivation_only must be true")
        if self.raw_transcript_committed:
            errors.append("raw_transcript_committed must be false")
        if not self.source_hashes:
            errors.append("at least one source_hash is required")
        if any(not item.strip() for item in self.source_hashes):
            errors.append("source_hashes cannot contain blank values")
        payload = {
            "schema": "omega-chatmem-checkpoint-preflight/v1",
            "checkpoint_id": self.checkpoint_id,
            "previous_checkpoint": self.previous_checkpoint,
            "oak_status": self.oak_status,
            "public_derivation_only": self.public_derivation_only,
            "raw_transcript_committed": self.raw_transcript_committed,
            "source_hashes": list(self.source_hashes),
            "touched_systems": list(self.touched_systems),
            "errors": errors,
        }
        payload["status"] = "PASS" if not errors else "FAIL"
        payload["fingerprint"] = stable_digest(payload)
        return payload


def checkpoint_gate_handler(
    capability: Capability,
    inputs: Mapping[str, Any],
) -> HandlerResult:
    manifest = ChatMemCheckpointManifest.from_mapping(
        inputs.get("checkpoint_manifest", {})
    )
    validation = manifest.validate()
    if validation["status"] != "PASS":
        raise ValueError(
            "ChatMem checkpoint preflight failed: "
            + "; ".join(validation["errors"])
        )
    return HandlerResult(
        outputs={"checkpoint_gate": validation},
        notes=(
            "chatmem_oak_preflight=pass",
            "raw_transcript_committed=false",
            "public_derivation_only=true",
        ),
    )


def chatmem_capabilities() -> tuple[Capability, ...]:
    return (
        Capability(
            capability_id="chatmem.library_search_pointer",
            domains=("memory", "files", "chatgpt"),
            consumes=("pointer_query",),
            produces=("chatmem_pointer_candidates",),
            authority="read",
            quality=0.98,
            information_gain=0.98,
            verifiability=0.96,
            reuse=0.99,
            cost=0.08,
            latency=0.10,
            risk=0.05,
            alternatives=("chatmem.github_fetch_pointer",),
            failure_modes=("library_unavailable", "pointer_not_found"),
        ),
        Capability(
            capability_id="chatmem.github_fetch_pointer",
            domains=("memory", "github", "chatgpt"),
            consumes=("repo", "branch", "pointer_path"),
            produces=("chatmem_pointer_candidates",),
            authority="read",
            quality=0.97,
            information_gain=0.96,
            verifiability=0.99,
            reuse=0.98,
            cost=0.10,
            latency=0.12,
            risk=0.05,
            alternatives=(),
            failure_modes=("not_found", "permission_error"),
        ),
        Capability(
            capability_id="chatmem.library_search_context",
            domains=("memory", "files", "chatgpt"),
            consumes=("context_query",),
            produces=("chatmem_context_candidates",),
            authority="read",
            quality=0.98,
            information_gain=0.96,
            verifiability=0.95,
            reuse=0.99,
            cost=0.10,
            latency=0.12,
            risk=0.06,
            alternatives=("chatmem.github_fetch_context",),
            failure_modes=("library_unavailable", "context_not_found"),
        ),
        Capability(
            capability_id="chatmem.github_fetch_context",
            domains=("memory", "github", "chatgpt"),
            consumes=("repo", "branch", "context_path"),
            produces=("chatmem_context_candidates",),
            authority="read",
            quality=0.96,
            information_gain=0.92,
            verifiability=0.99,
            reuse=0.98,
            cost=0.10,
            latency=0.12,
            risk=0.05,
            alternatives=(),
            failure_modes=("not_found", "permission_error"),
        ),
        Capability(
            capability_id="chatmem.validate_checkpoint",
            domains=("memory", "chatgpt", "oak"),
            consumes=("checkpoint_manifest",),
            produces=("checkpoint_gate",),
            authority="read",
            quality=0.99,
            information_gain=0.95,
            verifiability=0.99,
            reuse=0.99,
            cost=0.02,
            latency=0.01,
            risk=0.01,
            alternatives=(),
            failure_modes=("privacy_gate_failed", "provenance_gate_failed"),
        ),
        Capability(
            capability_id="chatmem.library_upload_bundle",
            domains=("memory", "files", "chatgpt"),
            consumes=(
                "checkpoint_gate",
                "library_container_path",
                "library_destination",
            ),
            produces=("library_persistence_receipt",),
            authority="write",
            quality=0.97,
            information_gain=0.70,
            verifiability=0.95,
            reuse=0.94,
            cost=0.12,
            latency=0.18,
            risk=0.35,
            alternatives=(),
            failure_modes=("upload_failed", "permission_error"),
        ),
        Capability(
            capability_id="chatmem.github_create_checkpoint",
            domains=("memory", "github", "chatgpt"),
            consumes=(
                "checkpoint_gate",
                "repo",
                "branch",
                "checkpoint_path",
                "checkpoint_content",
                "commit_message",
            ),
            produces=("github_checkpoint_receipt",),
            authority="write",
            quality=0.98,
            information_gain=0.72,
            verifiability=0.99,
            reuse=0.96,
            cost=0.12,
            latency=0.18,
            risk=0.42,
            alternatives=(),
            failure_modes=("path_exists", "permission_error"),
        ),
        Capability(
            capability_id="chatmem.github_update_pointer",
            domains=("memory", "github", "chatgpt"),
            consumes=(
                "checkpoint_gate",
                "library_persistence_receipt",
                "github_checkpoint_receipt",
                "repo",
                "branch",
                "pointer_path",
                "pointer_content",
                "pointer_blob_sha",
                "pointer_commit_message",
            ),
            produces=("github_pointer_update_receipt",),
            authority="write",
            quality=0.99,
            information_gain=0.65,
            verifiability=0.99,
            reuse=0.98,
            cost=0.10,
            latency=0.15,
            risk=0.48,
            alternatives=(),
            failure_modes=("stale_blob_sha", "permission_error"),
        ),
    )


def chatmem_external_bindings() -> tuple[ExternalBinding, ...]:
    return (
        ExternalBinding(
            capability_id="chatmem.library_search_pointer",
            connector="files",
            action="search",
            external_authority="read",
            argument_template={
                "search_query": [{"q": "$pointer_query"}],
                "scope": {"surfaces": ["library"]},
                "top_k": 5,
            },
        ),
        ExternalBinding(
            capability_id="chatmem.github_fetch_pointer",
            connector="GitHub",
            action="fetch_file",
            external_authority="read",
            argument_template={
                "repository_full_name": "$repo",
                "path": "$pointer_path",
                "ref": "$branch",
                "encoding": "utf-8",
            },
        ),
        ExternalBinding(
            capability_id="chatmem.library_search_context",
            connector="files",
            action="search",
            external_authority="read",
            argument_template={
                "search_query": [{"q": "$context_query"}],
                "scope": {"surfaces": ["library"]},
                "top_k": 10,
            },
        ),
        ExternalBinding(
            capability_id="chatmem.github_fetch_context",
            connector="GitHub",
            action="fetch_file",
            external_authority="read",
            argument_template={
                "repository_full_name": "$repo",
                "path": "$context_path",
                "ref": "$branch",
                "encoding": "utf-8",
            },
        ),
        ExternalBinding(
            capability_id="chatmem.library_upload_bundle",
            connector="files",
            action="manage_library",
            external_authority="write",
            argument_template={
                "operations": [
                    {
                        "operation": "upload",
                        "container_path": "$library_container_path",
                        "destination_path": "$library_destination",
                        "overwrite": False,
                    }
                ]
            },
            notes=(
                "Persistent Library mutation: explicit write authorization required.",
            ),
        ),
        ExternalBinding(
            capability_id="chatmem.github_create_checkpoint",
            connector="GitHub",
            action="create_file",
            external_authority="write",
            argument_template={
                "repository_full_name": "$repo",
                "path": "$checkpoint_path",
                "content": "$checkpoint_content",
                "message": "$commit_message",
                "branch": "$branch",
            },
            notes=(
                "Creates one public-derived checkpoint artifact only after local OAK gate.",
            ),
        ),
        ExternalBinding(
            capability_id="chatmem.github_update_pointer",
            connector="GitHub",
            action="update_file",
            external_authority="write",
            argument_template={
                "repository_full_name": "$repo",
                "path": "$pointer_path",
                "content": "$pointer_content",
                "message": "$pointer_commit_message",
                "sha": "$pointer_blob_sha",
                "branch": "$branch",
            },
            notes=(
                "Consumes Library and GitHub checkpoint receipts before pointer mutation.",
            ),
        ),
    )


def chatmem_bootstrap_intent() -> Intent:
    return Intent(
        intent_id="CHATMEM-BOOTSTRAP-R04",
        available_inputs=(
            "pointer_query",
            "context_query",
            "repo",
            "branch",
            "pointer_path",
            "context_path",
        ),
        required_outputs=(
            "chatmem_pointer_candidates",
            "chatmem_context_candidates",
        ),
        domains=("memory", "chatgpt"),
        allow_mutation=False,
        allow_irreversible=False,
        max_steps=8,
    )


def chatmem_checkpoint_intent(*, allow_mutation: bool = False) -> Intent:
    return Intent(
        intent_id="CHATMEM-CHECKPOINT-R04",
        available_inputs=(
            "checkpoint_manifest",
            "library_container_path",
            "library_destination",
            "repo",
            "branch",
            "checkpoint_path",
            "checkpoint_content",
            "commit_message",
            "pointer_path",
            "pointer_content",
            "pointer_blob_sha",
            "pointer_commit_message",
        ),
        required_outputs=(
            "library_persistence_receipt",
            "github_checkpoint_receipt",
            "github_pointer_update_receipt",
        ),
        domains=("memory", "chatgpt"),
        allow_mutation=allow_mutation,
        allow_irreversible=False,
        max_steps=8,
    )


def default_chatmem_bootstrap_values(topic: str) -> dict[str, Any]:
    normalized = topic.strip() or "current Tristan work"
    return {
        "pointer_query": "CHATMEM_GLOBAL_POINTER Ω-CHATMEM-HGFM global pointer",
        "context_query": f"Ω-CHATMEM-HGFM relevant memory for {normalized}",
        "repo": DEFAULT_REPOSITORY,
        "branch": DEFAULT_BRANCH,
        "pointer_path": DEFAULT_POINTER_PATH,
        "context_path": DEFAULT_CONTEXT_PATH,
    }
