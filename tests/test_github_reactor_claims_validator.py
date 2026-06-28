from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "claims_validator.py"


def load_module():
    spec = importlib.util.spec_from_file_location("claims_validator", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["claims_validator"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_claims_validator_accepts_valid_claim(tmp_path):
    module = load_module()
    path = tmp_path / "claims.jsonl"
    path.write_text(
        '{"id":"C1","claim":"safe claim","domain":"ops","oak_status":"FERTILE","evidence":["doc"],"residue":[],"next_test":"review"}\n',
        encoding="utf-8",
    )
    assert module.validate_claims(path) == []


def test_claims_validator_reports_missing_fields(tmp_path):
    module = load_module()
    path = tmp_path / "claims.jsonl"
    path.write_text('{"id":"C1","claim":"incomplete"}\n', encoding="utf-8")
    findings = module.validate_claims(path)
    assert findings
    assert any("missing fields" in item.message for item in findings)


def test_claims_validator_reports_invalid_status(tmp_path):
    module = load_module()
    path = tmp_path / "claims.jsonl"
    path.write_text(
        '{"id":"C1","claim":"safe claim","domain":"ops","oak_status":"BAD","evidence":["doc"],"residue":[],"next_test":"review"}\n',
        encoding="utf-8",
    )
    findings = module.validate_claims(path)
    assert any("invalid oak_status" in item.message for item in findings)
