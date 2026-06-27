from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DOMAINS = (
    "automation",
    "energy",
    "materials",
    "signals",
    "software",
    "governance",
)

TOPICS = (
    "fractal graphs",
    "local workflows",
    "error correction",
    "wavelet features",
    "battery safety",
    "agent review",
    "public metadata",
    "prototype scoring",
)


@dataclass(frozen=True)
class DemoDataset:
    seed: int
    generated_sample_data: bool
    institutions: list[dict[str, Any]]
    topics: list[dict[str, Any]]
    publications: list[dict[str, Any]]
    patent_records: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def generate_demo_dataset(seed: int = 7, count: int = 8) -> DemoDataset:
    """Generate deterministic sample records with no private data.

    The output is synthetic and is intended for tests, tutorials, and local dry-runs.
    """

    rng = random.Random(seed)
    count = max(1, int(count))

    institutions = [
        {
            "institution_id": f"demo_inst_{idx:02d}",
            "name": f"Demo Research Node {idx}",
            "country": "Generated",
            "generated_sample_data": True,
        }
        for idx in range(1, 4)
    ]

    topics = [
        {
            "topic_id": f"demo_topic_{idx:02d}",
            "label": label,
            "domain": rng.choice(DOMAINS),
            "generated_sample_data": True,
        }
        for idx, label in enumerate(TOPICS[:count], start=1)
    ]

    publications: list[dict[str, Any]] = []
    patent_records: list[dict[str, Any]] = []

    for idx in range(1, count + 1):
        topic = topics[(idx - 1) % len(topics)]
        inst = institutions[(idx - 1) % len(institutions)]
        year = 2020 + (idx % 7)
        score = round(0.45 + rng.random() * 0.5, 4)
        publications.append(
            {
                "publication_id": f"demo_pub_{seed}_{idx:03d}",
                "title": f"Generated study on {topic['label']} #{idx}",
                "year": year,
                "institution_id": inst["institution_id"],
                "topic_id": topic["topic_id"],
                "evidence_level": "synthetic_fixture",
                "opportunity_score": score,
                "generated_sample_data": True,
            }
        )
        patent_records.append(
            {
                "patent_record_id": f"demo_pat_{seed}_{idx:03d}",
                "title": f"Generated invention pattern for {topic['label']} #{idx}",
                "year": year,
                "owner": "Demo Owner",
                "topic_id": topic["topic_id"],
                "status": rng.choice(("draft", "review_required", "public_ok")),
                "generated_sample_data": True,
            }
        )

    return DemoDataset(
        seed=seed,
        generated_sample_data=True,
        institutions=institutions,
        topics=topics,
        publications=publications,
        patent_records=patent_records,
    )


def write_demo_dataset(output_dir: str | Path, seed: int = 7, count: int = 8) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    dataset = generate_demo_dataset(seed=seed, count=count)

    files = {
        "dataset": output_path / "demo_dataset.json",
        "publications": output_path / "demo_publications.json",
        "patent_records": output_path / "demo_patent_records.json",
        "institutions": output_path / "demo_institutions.json",
        "topics": output_path / "demo_topics.json",
    }

    files["dataset"].write_text(dataset.to_json(), encoding="utf-8")
    files["publications"].write_text(json.dumps(dataset.publications, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files["patent_records"].write_text(json.dumps(dataset.patent_records, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files["institutions"].write_text(json.dumps(dataset.institutions, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files["topics"].write_text(json.dumps(dataset.topics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {key: str(value) for key, value in files.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic local sample data.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--output", default="outputs/demo_digest")
    args = parser.parse_args(argv)
    files = write_demo_dataset(args.output, seed=args.seed, count=args.count)
    print(json.dumps({"generated_sample_data": True, "files": files}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
