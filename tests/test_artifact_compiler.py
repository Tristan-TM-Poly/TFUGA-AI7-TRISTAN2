from tools.artifact_compiler import compile_idea_to_artifacts, slugify
from tools.reality_gradient import RealityLevel


def test_slugify_creates_safe_slug():
    assert slugify("Reality Forge!!!") == "reality_forge"


def test_compile_idea_creates_canonical_artifact_paths():
    compiled = compile_idea_to_artifacts("Reality Forge")
    assert compiled.artifacts.theory_doc == "docs/theories/reality_forge.md"
    assert compiled.artifacts.schema == "schemas/reality_forge.schema.json"
    assert compiled.artifacts.tool == "tools/reality_forge.py"
    assert compiled.artifacts.tests == "tests/test_reality_forge.py"
    assert compiled.artifacts.m_minus == "safety/m_minus_reality_forge.yaml"
    assert compiled.artifacts.oak_report == "docs/oak_reports/reality_forge_oak_report.md"


def test_compile_idea_with_no_touch_risk_blocks_execution():
    compiled = compile_idea_to_artifacts("medical dose automation")
    assert compiled.failures.no_touch_required
    assert compiled.safe_next_action.startswith("NO-TOUCH")


def test_compile_idea_local_test_upgrades_reality():
    compiled = compile_idea_to_artifacts("Testable Forge", has_local_test=True)
    assert compiled.reality.level == RealityLevel.R6_LOCAL_TEST
    assert len(compiled.counterworlds.worlds) == 6
