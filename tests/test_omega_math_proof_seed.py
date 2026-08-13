import json
from pathlib import Path


def test_book_of_proof_seed_is_small_provenance_first_mathir():
    path = Path("omega_math_proof_research_os/examples/book_of_proof_seed.jsonl")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) == 5
    assert len({record["artifact_id"] for record in records}) == 5
    assert all(record["oak_status"] == "source_extracted" for record in records)
    assert all(record["formal_status"] == "unformalized" for record in records)
    assert all(record["source_anchors"] for record in records)
    assert all(record["source_anchors"][0]["source_url"] == "conversation-upload://Main.pdf" for record in records)
