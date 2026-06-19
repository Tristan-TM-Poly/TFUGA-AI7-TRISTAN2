from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "schema_validator.py"


def load_module():
    spec = importlib.util.spec_from_file_location("schema_validator", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["schema_validator"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_repository_validator_accepts_minimal_valid_atlas(tmp_path):
    module = load_module()
    path = tmp_path / "repositories.yml"
    path.write_text(
        """
repositories:
  - name: Tristan-TM-Poly/example
    role: root_reactor
    priority: P0
    visibility: public
    oak_status: FERTILE
""",
        encoding="utf-8",
    )
    assert module.validate_repositories(path) == []


def test_repository_validator_reports_missing_fields(tmp_path):
    module = load_module()
    path = tmp_path / "repositories.yml"
    path.write_text(
        """
repositories:
  - name: Tristan-TM-Poly/example
    role: root_reactor
""",
        encoding="utf-8",
    )
    findings = module.validate_repositories(path)
    assert findings
    assert any("missing fields" in item.message for item in findings)


def test_hyperedge_validator_accepts_minimal_valid_atlas(tmp_path):
    module = load_module()
    path = tmp_path / "hyperedges.yml"
    path.write_text(
        """
hyperedges:
  - id: GHR-E-TEST
    label: TEST_EDGE
    transformation: test_transform
    oak_gate: review_required
    cvcd_gain: high
    risk: low
""",
        encoding="utf-8",
    )
    assert module.validate_hyperedges(path) == []
