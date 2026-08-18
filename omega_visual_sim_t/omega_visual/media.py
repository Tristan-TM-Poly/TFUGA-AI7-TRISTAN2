from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from typing import Any, Mapping

MEDIA_SCHEMA_VERSION = "0.1"
MEDIA_ATTACHMENT_PROTOCOL = "OMEGA-MEDIA-ATTACH/0.1"
REPRESENTATION_STATUSES = {"CANDIDATE", "MEASURED", "DERIVED", "VERIFIED"}
BASELINE_FAMILIES = {"FFT", "STFT", "CQT", "WAVELET"}
SUPPORTED_FAMILIES = BASELINE_FAMILIES | {"FFWT", "FFWT_HAC", "LEARNED", "OTHER"}
RIGHTS_MODES = {"owned", "licensed", "semantic_original"}


class MediaSpecError(ValueError):
    """Raised when an AudioVisualIR or MediaMicroscope capsule is inconsistent."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MediaSpecError(f"{path} must be an object")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise MediaSpecError(f"{path} must be a list")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MediaSpecError(f"{path} must be a non-empty string")
    return value.strip()


def _finite_number(value: Any, path: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise MediaSpecError(f"{path} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        raise MediaSpecError(f"{path} must be >= {minimum}")
    return number


def wrap_phase(angle_rad: float) -> float:
    """Wrap radians to (-pi, pi]."""
    angle = _finite_number(angle_rad, "angle_rad")
    wrapped = (angle + math.pi) % (2.0 * math.pi) - math.pi
    return math.pi if math.isclose(wrapped, -math.pi, abs_tol=1e-15) else wrapped


def amplitude_phase(real: float, imag: float) -> dict[str, float]:
    """Return the polar view of one complex coefficient."""
    re = _finite_number(real, "real")
    im = _finite_number(imag, "imag")
    return {"amplitude": math.hypot(re, im), "phase_rad": math.atan2(im, re)}


def relative_phase_graph(phases_rad: Mapping[str, float]) -> list[dict[str, Any]]:
    """Build pairwise wrapped phase relations without treating absolute phase as invariant."""
    if not isinstance(phases_rad, Mapping) or not phases_rad:
        raise MediaSpecError("phases_rad must be a non-empty mapping")
    labels = sorted(phases_rad)
    values = {label: _finite_number(phases_rad[label], f"phases_rad[{label!r}]") for label in labels}
    edges: list[dict[str, Any]] = []
    for index, left in enumerate(labels):
        for right in labels[index + 1 :]:
            edges.append(
                {
                    "from": left,
                    "to": right,
                    "delta_phase_rad": wrap_phase(values[right] - values[left]),
                }
            )
    return edges


def _validate_interval(record: dict[str, Any], path: str, duration_s: float) -> tuple[float, float]:
    start = _finite_number(record.get("start_s"), f"{path}.start_s", minimum=0.0)
    end = _finite_number(record.get("end_s"), f"{path}.end_s", minimum=0.0)
    if end <= start:
        raise MediaSpecError(f"{path}.end_s must be greater than start_s")
    if end > duration_s + 1e-9:
        raise MediaSpecError(f"{path}.end_s exceeds media.duration_s")
    return start, end


def _validate_timeline_records(
    values: Any,
    path: str,
    duration_s: float,
    *,
    label_field: str,
) -> tuple[list[dict[str, Any]], set[str]]:
    records = _list(values, path)
    out: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    previous_start = -1.0
    for index, raw in enumerate(records):
        record = deepcopy(_mapping(raw, f"{path}[{index}]"))
        identifier = _text(record.get("id"), f"{path}[{index}].id")
        _text(record.get(label_field), f"{path}[{index}].{label_field")
        start, _ = _validate_interval(record, f"{path}[{index}]", duration_s)
        if start < previous_start:
            raise MediaSpecError(f"{path} must be ordered by start_s")
        previous_start = start
        if identifier in identifiers:
            raise MediaSpecError(f"duplicate timeline id: {identifier}")
        identifiers.add(identifier)
        out.append(record)
    return out, identifiers


def validate_audio_visual_ir(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate a portable AudioVisualIR without pretending to perform transcription or FFWT."""
    root = deepcopy(_mapping(spec, "audio_visual_ir"))
    if root.get("schema_version") != MEDIA_SCHEMA_VERSION:
        raise MediaSpecError(f"schema_version must be {MEDIA_SCHEMA_VERSION}")

    media = _mapping(root.get("media"), "media")
    _text(media.get("id"), "media.id")
    _text(media.get("title"), "media.title")
    duration_s = _finite_number(media.get("duration_s"), "media.duration_s", minimum=0.0)
    if duration_s <= 0:
        raise MediaSpecError("media.duration_s must be > 0")
    _text(media.get("source_kind"), "media.source_kind")

    audio = _mapping(root.get("audio"), "audio")
    sample_rate = _finite_number(audio.get("sample_rate_hz"), "audio.sample_rate_hz", minimum=1.0)
    if not float(sample_rate).is_integer():
        raise MediaSpecError("audio.sample_rate_hz must be an integer-valued number")
    channels = audio.get("channels")
    if not isinstance(channels, int) or isinstance(channels, bool) or channels <= 0:
        raise MediaSpecError("audio.channels must be a positive integer")

    timeline = _mapping(root.get("timeline"), "timeline")
    phonemes, phoneme_ids = _validate_timeline_records(
        timeline.get("phonemes", []), "timeline.phonemes", duration_s, label_field="label"
    )
    words, word_ids = _validate_timeline_records(
        timeline.get("words", []), "timeline.words", duration_s, label_field="text"
    )
    for index, word in enumerate(words):
        refs = _list(word.get("phoneme_ids", []), f"timeline.words[{index}].phoneme_ids")
        unknown = sorted(set(refs) - phoneme_ids)
        if unknown:
            raise MediaSpecError(
                f"timeline.words[{index}] references unknown phoneme ids: {', '.join(unknown)}"
            )
    timeline["phonemes"] = phonemes
    timeline["words"] = words
    timeline.setdefault("semantic_beats", [])
    _list(timeline["semantic_beats"], "timeline.semantic_beats")
    root["timeline"] = timeline

    representations = _list(audio.get("representations"), "audio.representations")
    if not representations:
        raise MediaSpecError("audio.representations must not be empty")
    representation_ids: set[str] = set()
    families: set[str] = set()
    for index, raw in enumerate(representations):
        rep = _mapping(raw, f"audio.representations[{index}]")
        rep_id = _text(rep.get("id"), f"audio.representations[{index}].id")
        if rep_id in representation_ids:
            raise MediaSpecError(f"duplicate representation id: {rep_id}")
        representation_ids.add(rep_id)
        family = _text(rep.get("family"), f"audio.representations[{index}].family").upper()
        if family not in SUPPORTED_FAMILIES:
            raise MediaSpecError(f"unsupported representation family: {family}")
        families.add(family)
        status = _text(
            rep.get("epistemic_status"), f"audio.representations[{index}].epistemic_status"
        ).upper()
        if status not in REPRESENTATION_STATUSES:
            raise MediaSpecError(f"unsupported representation status: {status}")
        preserves = {
            _text(value, f"audio.representations[{index}].preserves")
            for value in _list(rep.get("preserves"), f"audio.representations[{index}].preserves")
        }
        if family in {"FFWT", "FFWT_HAC"} and not {"amplitude", "phase"}.issubset(preserves):
            raise MediaSpecError(f"{family} representation must explicitly preserve amplitude and phase")
        evidence_refs = _list(rep.get("evidence_refs", []), f"audio.representations[{index}].evidence_refs")
        if status == "VERIFIED" and not evidence_refs:
            raise MediaSpecError(f"VERIFIED representation {rep_id} requires evidence_refs")

    if families & {"FFWT", "FFWT_HAC"} and not families & BASELINE_FAMILIES:
        raise MediaSpecError("FFWT candidates require at least one declared FFT/STFT/CQT/WAVELET baseline")

    features = _mapping(audio.get("features", {}), "audio.features")
    for field in ("pitch_hz", "formants_hz", "phase_relations"):
        features.setdefault(field, [])
        _list(features[field], f"audio.features.{field}")
    audio["features"] = features
    root["audio"] = audio

    video = _mapping(root.get("video", {}), "video")
    video.setdefault("scenes", [])
    _list(video["scenes"], "video.scenes")
    root["video"] = video

    links = _list(root.get("links", []), "links")
    known_ids = phoneme_ids | word_ids | representation_ids
    for index, raw in enumerate(links):
        link = _mapping(raw, f"links[{index}]")
        source = _text(link.get("from_id"), f"links[{index}].from_id")
        target = _text(link.get("to_id"), f"links[{index}].to_id")
        _text(link.get("relation"), f"links[{index}].relation")
        unknown = [identifier for identifier in (source, target) if identifier not in known_ids]
        if unknown:
            raise MediaSpecError(f"links[{index}] references unknown ids: {', '.join(unknown)}")

    provenance = _mapping(root.get("provenance"), "provenance")
    digest = _text(provenance.get("input_sha256"), "provenance.input_sha256")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
        raise MediaSpecError("provenance.input_sha256 must be a SHA-256 hex digest")
    rights_mode = _text(provenance.get("rights_mode"), "provenance.rights_mode")
    if rights_mode not in RIGHTS_MODES:
        raise MediaSpecError(f"unsupported provenance.rights_mode: {rights_mode}")

    oak = _mapping(root.get("oak"), "oak")
    if oak.get("analysis_is_measurement") is not False:
        raise MediaSpecError("oak.analysis_is_measurement must be false")
    if oak.get("representation_is_truth") is not False:
        raise MediaSpecError("oak.representation_is_truth must be false")
    if oak.get("ffwt_superiority_claimed") is not False:
        raise MediaSpecError("oak.ffwt_superiority_claimed must be false")

    return root


def compile_media_capsule(spec: dict[str, Any]) -> dict[str, Any]:
    """Compile AudioVisualIR into a content-addressed browser attachment contract."""
    ir = validate_audio_visual_ir(spec)
    ir_sha256 = _sha256(ir)
    representations = ir["audio"]["representations"]
    families = sorted({rep["family"].upper() for rep in representations})
    panels = ["video", "waveform", "timeline", "words", "phonemes"]
    preserves = {value for rep in representations for value in rep["preserves"]}
    if "amplitude" in preserves:
        panels.append("amplitude")
    if "phase" in preserves:
        panels.extend(["phase", "phase_graph"])
    panels.extend(["pitch", "formants"])

    return {
        "protocol": MEDIA_ATTACHMENT_PROTOCOL,
        "capsule_id": f"{ir['media']['id']}@{ir_sha256[:16]}",
        "ir_sha256": ir_sha256,
        "audio_visual_ir": ir,
        "attachment": {
            "slot": "MediaMicroscopeSlot",
            "actions": ["inspect", "seek", "zoom", "compare", "fork", "reset"],
            "panels": panels,
            "synchronization_key": "time_s",
        },
        "representation_portfolio": {
            "families": families,
            "baseline_required_for_ffwt": True,
            "selection_policy": "question_conditioned_and_oak_benchmarked",
        },
        "oak": {
            "analysis_is_measurement": False,
            "representation_is_truth": False,
            "ffwt_superiority_claimed": False,
            "phase_absolute_is_invariant": False,
            "relative_phase_available": bool(ir["audio"]["features"]["phase_relations"]),
        },
    }
