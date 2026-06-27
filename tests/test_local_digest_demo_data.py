from __future__ import annotations

import json

from local_digest.demo_data import generate_demo_dataset, write_demo_dataset


def test_demo_dataset_is_deterministic() -> None:
    first = generate_demo_dataset(seed=42, count=5).to_dict()
    second = generate_demo_dataset(seed=42, count=5).to_dict()
    third = generate_demo_dataset(seed=43, count=5).to_dict()

    assert first == second
    assert first != third
    assert first["generated_sample_data"] is True


def test_demo_dataset_contains_expected_sections() -> None:
    data = generate_demo_dataset(seed=7, count=4).to_dict()

    assert len(data["publications"]) == 4
    assert len(data["patent_records"]) == 4
    assert len(data["institutions"]) == 3
    assert len(data["topics"]) == 4
    assert all(record["generated_sample_data"] for record in data["publications"])
    assert all(record["generated_sample_data"] for record in data["patent_records"])


def test_write_demo_dataset(tmp_path) -> None:
    files = write_demo_dataset(tmp_path, seed=5, count=3)

    assert set(files) == {"dataset", "publications", "patent_records", "institutions", "topics"}
    dataset = json.loads((tmp_path / "demo_dataset.json").read_text(encoding="utf-8"))
    publications = json.loads((tmp_path / "demo_publications.json").read_text(encoding="utf-8"))

    assert dataset["seed"] == 5
    assert len(publications) == 3
    assert dataset["generated_sample_data"] is True
