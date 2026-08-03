from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable, Mapping

from omega_web_hg_t.models import stable_id, utc_now

R03_SCHEMA = "omega-web-hg-absorption/0.3"


def text_digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ClaimCandidate:
    claim_id: str
    page_id: str
    section_id: str
    evidence_id: str
    url: str
    locator: str
    text: str
    text_sha256: str
    word_count: int
    epistemic_status: str = "extracted_claim_candidate_not_verified"


@dataclass(frozen=True)
class DuplicateRecord:
    duplicate_id: str
    kind: str
    representative_id: str
    member_id: str
    distance: int
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass
class AbsorptionBundle:
    source_run: str
    claims: list[ClaimCandidate]
    duplicates: list[DuplicateRecord]
    graph: dict[str, object]
    report: dict[str, object]
    created_at: str = field(default_factory=utc_now)

    @staticmethod
    def _write_jsonl(path: Path, records: Iterable[object]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                payload = asdict(record) if hasattr(record, "__dataclass_fields__") else record
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def write(self, output_dir: str | Path) -> Path:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        self._write_jsonl(root / "claim-candidates.jsonl", self.claims)
        self._write_jsonl(root / "duplicates.jsonl", self.duplicates)
        (root / "absorption-hypergraph.json").write_text(
            json.dumps(self.graph, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (root / "absorption-report.json").write_text(
            json.dumps(self.report, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        manifest = {
            "schema": R03_SCHEMA,
            "created_at": self.created_at,
            "source_run": self.source_run,
            "claims": len(self.claims),
            "duplicates": len(self.duplicates),
            "outputs": [
                "claim-candidates.jsonl",
                "duplicates.jsonl",
                "absorption-hypergraph.json",
                "absorption-report.json",
                "search.sqlite3",
            ],
            "boundary": "Claim candidates are extracted text spans, not verified propositions or factual certification.",
        }
        (root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return root


def claim_id(section_id: str, text: str) -> str:
    return stable_id("claim", section_id, text_digest(text))
