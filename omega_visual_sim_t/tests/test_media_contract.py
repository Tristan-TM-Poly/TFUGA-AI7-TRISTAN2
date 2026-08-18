import hashlib
import math
import unittest

from omega_visual.media import (
    MEDIA_ATTACHMENT_PROTOCOL,
    MediaSpecError,
    amplitude_phase,
    compile_media_capsule,
    relative_phase_graph,
    validate_audio_visual_ir,
)


def fixture():
    return {
        "schema_version": "0.1",
        "media": {
            "id": "speech-demo",
            "title": "Speech demo",
            "duration_s": 1.0,
            "source_kind": "video_audio_track",
        },
        "audio": {
            "sample_rate_hz": 48000,
            "channels": 1,
            "representations": [
                {
                    "id": "stft-baseline",
                    "family": "STFT",
                    "epistemic_status": "DERIVED",
                    "preserves": ["amplitude", "phase"],
                    "evidence_refs": [],
                },
                {
                    "id": "ffwt-candidate",
                    "family": "FFWT",
                    "epistemic_status": "CANDIDATE",
                    "preserves": ["amplitude", "phase", "scale"],
                    "evidence_refs": [],
                },
            ],
            "features": {
                "pitch_hz": [{"time_s": 0.1, "value": 120.0}],
                "formants_hz": [{"time_s": 0.1, "f1": 700.0, "f2": 1200.0}],
                "phase_relations": relative_phase_graph({"f0": 0.0, "h2": math.pi / 2}),
            },
        },
        "timeline": {
            "phonemes": [
                {"id": "p1", "label": "b", "start_s": 0.0, "end_s": 0.1},
                {"id": "p2", "label": "a", "start_s": 0.1, "end_s": 0.4},
            ],
            "words": [
                {
                    "id": "w1",
                    "text": "ba",
                    "start_s": 0.0,
                    "end_s": 0.4,
                    "phoneme_ids": ["p1", "p2"],
                }
            ],
            "semantic_beats": [],
        },
        "video": {"scenes": []},
        "links": [
            {"from_id": "w1", "to_id": "ffwt-candidate", "relation": "analyzed_by"},
        ],
        "provenance": {
            "input_sha256": hashlib.sha256(b"speech-demo").hexdigest(),
            "rights_mode": "owned",
        },
        "oak": {
            "analysis_is_measurement": False,
            "representation_is_truth": False,
            "ffwt_superiority_claimed": False,
        },
    }


class MediaContractTests(unittest.TestCase):
    def test_amplitude_phase_preserves_complex_coefficient(self):
        polar = amplitude_phase(3.0, 4.0)
        self.assertAlmostEqual(polar["amplitude"], 5.0)
        self.assertAlmostEqual(polar["phase_rad"], math.atan2(4.0, 3.0))

    def test_relative_phase_graph_uses_wrapped_relations(self):
        edges = relative_phase_graph({"a": math.pi * 0.9, "b": -math.pi * 0.9})
        self.assertEqual(len(edges), 1)
        self.assertAlmostEqual(edges[0]["delta_phase_rad"], math.pi * 0.2)

    def test_ffwt_requires_baseline(self):
        spec = fixture()
        spec["audio"]["representations"] = [spec["audio"]["representations"][1]]
        with self.assertRaisesRegex(MediaSpecError, "require at least one"):
            validate_audio_visual_ir(spec)

    def test_verified_representation_requires_evidence(self):
        spec = fixture()
        spec["audio"]["representations"][1]["epistemic_status"] = "VERIFIED"
        with self.assertRaisesRegex(MediaSpecError, "requires evidence_refs"):
            validate_audio_visual_ir(spec)

    def test_word_phoneme_references_are_checked(self):
        spec = fixture()
        spec["timeline"]["words"][0]["phoneme_ids"].append("missing")
        with self.assertRaisesRegex(MediaSpecError, "unknown phoneme"):
            validate_audio_visual_ir(spec)

    def test_oak_refuses_ffwt_superiority_claim(self):
        spec = fixture()
        spec["oak"]["ffwt_superiority_claimed"] = True
        with self.assertRaisesRegex(MediaSpecError, "must be false"):
            validate_audio_visual_ir(spec)

    def test_media_capsule_is_content_addressed_and_interactive(self):
        capsule = compile_media_capsule(fixture())
        self.assertEqual(capsule["protocol"], MEDIA_ATTACHMENT_PROTOCOL)
        self.assertEqual(capsule["attachment"]["slot"], "MediaMicroscopeSlot")
        self.assertIn("phase_graph", capsule["attachment"]["panels"])
        self.assertIn("STFT", capsule["representation_portfolio"]["families"])
        self.assertIn("FFWT", capsule["representation_portfolio"]["families"])
        self.assertFalse(capsule["oak"]["ffwt_superiority_claimed"])
        self.assertTrue(capsule["oak"]["relative_phase_available"])


if __name__ == "__main__":
    unittest.main()
