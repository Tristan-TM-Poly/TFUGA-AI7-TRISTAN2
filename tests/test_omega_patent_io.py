import json

from omega_patent_thesis_t.io import load_seed
from omega_patent_thesis_t.seed import example_seed


def test_load_seed(tmp_path):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(example_seed().to_dict()), encoding="utf-8")
    loaded = load_seed(path)
    assert loaded.patent_id == "EXAMPLE-PATENT-T"
