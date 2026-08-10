import json
from pathlib import Path

from omega_chatmem_hgfm_t.core import (
    load_conversations,
    recall,
    redact_secrets,
    run_pipeline,
    stable_id,
)


FIXTURE = Path(__file__).parent / "fixtures" / "chatgpt_export_minimal.json"


def test_load_official_export_shape():
    convs = load_conversations(FIXTURE)
    assert len(convs) == 1
    assert convs[0]["id"] == "conv-demo-1"
    assert [m["role"] for m in convs[0]["messages"]] == ["user", "assistant"]


def test_redaction_is_deterministic_and_removes_secret():
    text = "token=sk-proj-THIS_IS_A_SYNTHETIC_SECRET_123456"
    safe, count = redact_secrets(text)
    assert count >= 1
    assert "sk-proj-" not in safe
    assert "[REDACTED_SECRET]" in safe


def test_stable_id_reproducible():
    assert stable_id("x", "abc", 1) == stable_id("x", "abc", 1)
    assert stable_id("x", "abc", 1) != stable_id("x", "abc", 2)


def test_pipeline_generates_oak_safe_graph(tmp_path):
    out = tmp_path / "memory"
    result = run_pipeline(FIXTURE, out)
    assert result.node_count >= 4
    assert (out / "hgfm" / "nodes.jsonl").exists()
    assert (out / "hgfm" / "hyperedges.jsonl").exists()
    assert (out / "hgfm" / "provenance.jsonl").exists()
    assert (out / "canon" / "MEMORY_CAPSULE.md").exists()
    report = json.loads((out / "reports" / "oak_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["secret_redactions"] >= 1
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*") if p.is_file())
    assert "THIS_IS_A_SYNTHETIC_SECRET_123456" not in corpus
    nodes = [json.loads(line) for line in (out / "hgfm" / "nodes.jsonl").read_text(encoding="utf-8").splitlines()]
    assert not any(n.get("label") in {"REDACTED_SECRET", "SECRET"} for n in nodes)
    assert not any(n.get("kind") in {"Decision", "NextAction"} and "[REDACTED_SECRET]" in n.get("text", "") for n in nodes)


def test_recall_returns_related_subgraph(tmp_path):
    out = tmp_path / "memory"
    run_pipeline(FIXTURE, out)
    result = recall(out, "CHATMEM")
    assert result["matches"]
    labels = {n["label"] for n in result["matches"]}
    assert any("CHATMEM" in label for label in labels)
