import gzip
import json
from pathlib import Path

from omega_org_fam_t.atlas import compile_atlas


def _count_jsonl_gz(paths):
    count = 0
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                json.loads(line)
                count += 1
    return count


def test_massive_atlas_streams_and_links_records(tmp_path: Path):
    output = tmp_path / "atlas"
    manifest = compile_atlas(
        output,
        family_records=4_096,
        family_shard_size=1_024,
        evidence_shard_size=3_072,
    )
    family_paths = sorted((output / "families").glob("*.jsonl.gz"))
    evidence_paths = sorted((output / "evidence").glob("*.jsonl.gz"))
    assert manifest["family_records"] == 4_096
    assert manifest["evidence_records"] == 12_288
    assert manifest["total_objects"] == 16_384
    assert _count_jsonl_gz(family_paths) == 4_096
    assert _count_jsonl_gz(evidence_paths) == 12_288
    assert manifest["generator"]["permanent_total_ceiling"] is None
