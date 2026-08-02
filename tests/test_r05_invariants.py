from dataclasses import asdict
import json

from omega_re_t import r05_cli
from omega_re_t.public_receipts_r05 import BITS, generate_keypair
from omega_re_t.re1024_calibration_r05 import deterministic_re1024_fixture


def test_lamport_key_has_256_pairs():
    key = generate_keypair(b"0123456789abcdef-invariant")
    assert len(key.public_key.commitments) == BITS
    assert len(key.secrets) == BITS


def test_demo_json_roundtrip_is_stable():
    payload = r05_cli.all_demos()
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert decoded["schema"] == payload["schema"]
    assert decoded["boundaries"] == payload["boundaries"]


def test_re1024_has_sixteen_families():
    fixture = deterministic_re1024_fixture()
    assert len({item.family for item in fixture}) == 16
    counts = {family: 0 for family in {item.family for item in fixture}}
    for item in fixture:
        counts[item.family] += 1
    assert set(counts.values()) == {64}


def test_all_outputs_are_serialisable():
    json.dumps(r05_cli.all_demos(), sort_keys=True)
