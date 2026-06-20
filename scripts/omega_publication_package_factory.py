#!/usr/bin/env python3
"""
Omega Publication Package Factory.

Transforms a Tristan Publication Atlas manifest into OAK-safe publication packages:
concept notes, paper outlines, dataset plans, prototype plans, validation plans,
and human-review checklists.

Boundary:
- Does not send emails or contact anyone.
- Does not claim professor endorsement, collaboration, or acceptance.
- Generates reviewable drafts and planning artifacts only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_TEMPLATES: Dict[str, Any] = {
    "version": "omega.publication_package_templates.v1",
    "default_sections": [
        "abstract_seed",
        "problem_statement",
        "related_public_work",
        "tristan_contribution",
        "methodology",
        "data_plan",
        "prototype_plan",
        "oak_validation_plan",
        "negative_memory_plan",
        "submission_readiness"
    ],
    "project_angles": {
        "omega_math_universe": {
            "claim_style": "formal scaffold plus executable validation",
            "core_question": "Can generative mathematical structures be represented as OAK-auditable hypergraph traces?",
            "prototype": "claim-card schema, theorem/conjecture bank, and proof-status classifier"
        },
        "omega_spectro_universe": {
            "claim_style": "measurement-first signal pipeline",
            "core_question": "Can FFWT/HAC/CVCD descriptors improve spectroscopy compression, classification, denoising, or anomaly detection?",
            "prototype": "spectroscopy dataset manifest, feature extractor, baseline comparison, and residue audit"
        },
        "omega_materials": {
            "claim_style": "candidate-materials scaffold, not phase discovery claim",
            "core_question": "Can fractal/topological descriptors produce useful candidate features for materials datasets?",
            "prototype": "crystal/graph descriptor pack, simple baselines, and falsification tests"
        },
        "ait_dynamics": {
            "claim_style": "dynamics benchmark and reproducible simulator",
            "core_question": "Can AIT-generated models produce testable dynamics benchmarks without overclaiming?",
            "prototype": "ODE/PDE toy systems, conserved quantities, stability traces, and failure cases"
        },
        "bayes_tristan": {
            "claim_style": "probabilistic decision layer",
            "core_question": "Can hypotheses be scored over truth, utility, testability, safety, novelty, and compressibility without confusing fertility with proof?",
            "prototype": "Bayes-Tristan posterior card, action selector, and negative-memory updater"
        },
        "hgfm": {
            "claim_style": "hypergraph representation and graph-learning benchmark",
            "core_question": "Can nested hypergraph/fractal/mycelial representations improve traceability across ideas, data, code, and validation?",
            "prototype": "HGFM JSON schema, graph export, traversal metrics, and stability matrix"
        },
        "ait_code_science": {
            "claim_style": "code-generation benchmark with strict validation",
            "core_question": "Can math-to-code generation be made auditable through tests, schemas, manifests, and OAK gates?",
            "prototype": "multi-language code generator, tests, CI artifacts, and correctness residues"
        }
    },
    "readiness_thresholds": {
        "weak": 2.0,
        "promising": 5.0,
        "strong": 8.0
    }
}


@dataclass
class PackageRecord:
    package_id: str
    project_key: str
    project_title: str
    institution: str
    author: str
    score: float
    package_dir: str
    files: List[str] = field(default_factory=list)
    readiness: str = "weak"
    residues: List[str] = field(default_factory=list)

    def to_jsonable(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def safe_slug(text: str) -> str:
    text = str(text or "").strip().replace("'", "")
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower() or "item"


def stable_id(*parts: str, length: int = 18) -> str:
    return hashlib.sha256("||".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:length]


def load_json(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if default is not None:
        return default
    raise FileNotFoundError(path)


def classify_readiness(score: float, thresholds: Dict[str, float]) -> str:
    if score >= thresholds.get("strong", 8.0):
        return "strong_candidate"
    if score >= thresholds.get("promising", 5.0):
        return "promising_candidate"
    if score >= thresholds.get("weak", 2.0):
        return "weak_candidate"
    return "needs_more_evidence"


def work_lines(match: Dict[str, Any], limit: int = 6) -> str:
    works = match.get("works") or []
    if not works:
        return "- No public works attached in this atlas run."
    lines = []
    for work in works[:limit]:
        year = work.get("publication_year") or "n.d."
        title = work.get("title") or "Untitled work"
        url = work.get("landing_url") or work.get("doi") or work.get("openalex_id") or ""
        lines.append(f"- {year}: {title} ({url})")
    return "\n".join(lines)


def author_name(match: Dict[str, Any]) -> str:
    author = match.get("author")
    if isinstance(author, dict) and author.get("display_name"):
        return author["display_name"]
    return "institution-level research node"


def institution_name(match: Dict[str, Any]) -> str:
    institution = match.get("institution") or {}
    return institution.get("display_name") or "Unknown institution"


def matched_terms(match: Dict[str, Any]) -> str:
    terms = match.get("matched_terms") or []
    return ", ".join(terms) if terms else "none"


def residues(match: Dict[str, Any]) -> List[str]:
    out = list(match.get("residues") or [])
    if not match.get("works"):
        out.append("no_public_works_in_package")
    if not match.get("matched_terms"):
        out.append("no_keyword_overlap")
    return sorted(set(out))


def project_angle(templates: Dict[str, Any], project_key: str) -> Dict[str, str]:
    return templates.get("project_angles", {}).get(project_key, {
        "claim_style": "OAK-safe research scaffold",
        "core_question": "What testable contribution can be built from this Tristan project?",
        "prototype": "minimal reproducible prototype plus validation manifest"
    })


def abstract_seed(match: Dict[str, Any], angle: Dict[str, str]) -> str:
    return f"""# Abstract Seed

This package proposes an OAK-safe research direction connecting **{match.get('project_title', match.get('project_key'))}** with public research metadata from **{institution_name(match)}** and **{author_name(match)}**.

Core question: {angle['core_question']}

The claim style is deliberately bounded: **{angle['claim_style']}**. The goal is not to assert a solved theory, but to define a falsifiable contribution, a reproducible prototype, and a negative-memory path for failed assumptions.
"""


def paper_outline(match: Dict[str, Any], angle: Dict[str, str]) -> str:
    return f"""# Paper Outline

## Working title

{match.get('project_title', match.get('project_key'))}: An OAK-Safe Research Package for {institution_name(match)}

## 1. Problem

Define the scientific or methodological gap that this package addresses, using public metadata only as orientation.

## 2. Related public work

{work_lines(match)}

## 3. Tristan contribution

- Project: `{match.get('project_key')}`
- Contribution style: {angle['claim_style']}
- Core question: {angle['core_question']}
- Matched terms: {matched_terms(match)}

## 4. Method

1. Build a minimal reproducible prototype.
2. Attach public/open-data manifests where possible.
3. Compare against a simple baseline.
4. Log failures as negative memory.
5. Promote only claims that survive OAK gates.

## 5. Evaluation

- Baseline comparison.
- Ablation study.
- Error/residue report.
- Reproducibility checklist.
- Human review of relevance and claims.

## 6. Limitations

This package does not imply professor endorsement, collaboration, acceptance, or validation.
"""


def dataset_plan(match: Dict[str, Any]) -> str:
    return f"""# Dataset Plan

## Dataset search targets

- Public repositories: Zenodo, DataCite, OpenML, RCSB when relevant, and discipline-specific repositories.
- Query expansion from matched terms: {matched_terms(match)}
- Institution/public-work context: {institution_name(match)} / {author_name(match)}

## Required metadata

- Source URL.
- License hint.
- Download URL if permitted.
- Size.
- Checksum.
- Schema or file format.
- Citation/DOI when available.

## OAK data gates

- License review passed.
- Provenance review passed.
- Format/schema validated.
- Baseline can run.
- Failure cases logged.
"""


def prototype_plan(match: Dict[str, Any], angle: Dict[str, str]) -> str:
    return f"""# Prototype Plan

Prototype seed: {angle['prototype']}

## Minimum viable artifact

- One script or notebook-free Python module.
- One config file.
- One public-data manifest.
- One test file.
- One CI workflow.
- One result artifact.

## Success criterion

The prototype must produce a measurable output that can be compared to a baseline. If no baseline is available, the package remains OAK-4 maximum.
"""


def oak_validation_plan(match: Dict[str, Any], readiness: str, package_residues: List[str]) -> str:
    residue_lines = "\n".join(f"- {item}" for item in package_residues) or "- none"
    return f"""# OAK Validation Plan

## Current readiness

`{readiness}`

## Gates

- OAK-1: idea captured.
- OAK-2: definitions separated from metaphors.
- OAK-3: testable scaffold exists.
- OAK-4: executable artifact exists.
- OAK-5: public-data validation and baseline comparison.
- OAK-6: external/domain review.
- OAK-7+: published/reproduced result.

## Residues

{residue_lines}

## Anti-illusion rules

- Do not call a match a collaboration.
- Do not call a prototype a proof.
- Do not call a dataset hit a validated benchmark.
- Do not contact anyone before human review.
"""


def review_checklist(match: Dict[str, Any]) -> str:
    return f"""# Human Review Checklist

## Target relevance

- [ ] Institution is correctly identified: {institution_name(match)}
- [ ] Public author/research node is correctly identified: {author_name(match)}
- [ ] Works are relevant and not false positives.
- [ ] Project fit is real, not just keyword overlap.

## Publication readiness

- [ ] Claim is bounded.
- [ ] Data source is legal and cited.
- [ ] Prototype exists or is clearly scoped.
- [ ] Baseline exists.
- [ ] Limitations are explicit.
- [ ] No message is sent automatically.

## Submission/contact boundary

- [ ] Human has reviewed professor/lab page.
- [ ] Human has reviewed journal/conference scope.
- [ ] Human has approved any message before sending.
"""


def collaboration_note(match: Dict[str, Any]) -> str:
    return f"""# Reviewable Collaboration Note Draft

This is a draft for human review only. It must not be sent automatically.

Hello,

I am preparing an OAK-safe research package around **{match.get('project_title', match.get('project_key'))}** and noticed public research metadata associated with **{institution_name(match)}** / **{author_name(match)}** that appears adjacent to this direction.

The package is framed conservatively: it includes a reproducible prototype plan, an open-data plan, and an explicit falsification/residue log. I am not treating this as a proven result; the goal is to make the idea easy to inspect, test, and reject or improve.

Potential fit terms: {matched_terms(match)}

Before contacting anyone, this note should be reviewed for relevance, accuracy, tone, and consent boundaries.
"""


def write_package(match: Dict[str, Any], templates: Dict[str, Any], out_dir: Path) -> PackageRecord:
    project_key = match.get("project_key", "unknown_project")
    project_title = match.get("project_title", project_key)
    inst = institution_name(match)
    author = author_name(match)
    score = float(match.get("score") or 0.0)
    readiness = classify_readiness(score, templates.get("readiness_thresholds", {}))
    package_residues = residues(match)
    angle = project_angle(templates, project_key)
    package_id = stable_id(project_key, inst, author, str(score))
    package_dir = out_dir / safe_slug(inst) / safe_slug(project_key) / safe_slug(author)
    package_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "00_PACKAGE_INDEX.md": package_index(match, readiness, package_residues),
        "01_ABSTRACT_SEED.md": abstract_seed(match, angle),
        "02_PAPER_OUTLINE.md": paper_outline(match, angle),
        "03_DATASET_PLAN.md": dataset_plan(match),
        "04_PROTOTYPE_PLAN.md": prototype_plan(match, angle),
        "05_OAK_VALIDATION_PLAN.md": oak_validation_plan(match, readiness, package_residues),
        "06_HUMAN_REVIEW_CHECKLIST.md": review_checklist(match),
        "07_COLLABORATION_NOTE_DRAFT_REVIEW_ONLY.md": collaboration_note(match),
        "package.json": json.dumps({
            "version": "omega.publication_package.v1",
            "package_id": package_id,
            "project_key": project_key,
            "project_title": project_title,
            "institution": inst,
            "author": author,
            "score": score,
            "readiness": readiness,
            "residues": package_residues,
            "source_match": match,
            "boundary": {
                "review_only": True,
                "no_automatic_contact": True,
                "no_endorsement_claim": True
            }
        }, indent=2, ensure_ascii=False) + "\n",
    }
    written: List[str] = []
    for name, content in files.items():
        path = package_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))
    return PackageRecord(
        package_id=package_id,
        project_key=project_key,
        project_title=project_title,
        institution=inst,
        author=author,
        score=score,
        package_dir=str(package_dir),
        files=written,
        readiness=readiness,
        residues=package_residues,
    )


def package_index(match: Dict[str, Any], readiness: str, package_residues: List[str]) -> str:
    residue_lines = "\n".join(f"- {item}" for item in package_residues) or "- none"
    return f"""# Publication Package Index

## Target

- Project: `{match.get('project_key')}` / {match.get('project_title')}
- Institution: {institution_name(match)}
- Public author/research node: {author_name(match)}
- Heuristic score: {match.get('score')}
- Readiness: `{readiness}`

## Files

1. `01_ABSTRACT_SEED.md`
2. `02_PAPER_OUTLINE.md`
3. `03_DATASET_PLAN.md`
4. `04_PROTOTYPE_PLAN.md`
5. `05_OAK_VALIDATION_PLAN.md`
6. `06_HUMAN_REVIEW_CHECKLIST.md`
7. `07_COLLABORATION_NOTE_DRAFT_REVIEW_ONLY.md`
8. `package.json`

## Matched terms

{matched_terms(match)}

## Residues

{residue_lines}

## Boundary

This is a review-only publication package. It is not an email, not a submission, not an endorsement, and not a collaboration claim.
"""


def write_dashboard(records: List[PackageRecord], out_dir: Path) -> None:
    ranked = sorted(records, key=lambda r: r.score, reverse=True)
    lines = ["# Omega Publication Package Factory Dashboard", "", f"Generated packages: {len(records)}", "", "## Top packages", ""]
    for record in ranked[:100]:
        lines.append(f"- **{record.project_title}** × **{record.institution}** × `{record.author}` — `{record.readiness}` score `{record.score}`")
    (out_dir / "PUBLICATION_PACKAGE_DASHBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_packages(atlas_manifest: Path, template_path: Optional[Path], out_dir: Path, min_score: float, top_k: int) -> List[PackageRecord]:
    atlas = load_json(atlas_manifest)
    templates = load_json(template_path, DEFAULT_TEMPLATES) if template_path else DEFAULT_TEMPLATES
    matches = atlas.get("matches") or []
    selected = [m for m in matches if float(m.get("score") or 0.0) >= min_score]
    selected = sorted(selected, key=lambda m: float(m.get("score") or 0.0), reverse=True)[:top_k]
    out_dir.mkdir(parents=True, exist_ok=True)
    records = [write_package(match, templates, out_dir / "packages") for match in selected]
    manifest = {
        "version": "omega.publication_package_factory.v1",
        "created_unix": time.time(),
        "source_atlas": str(atlas_manifest),
        "package_count": len(records),
        "min_score": min_score,
        "top_k": top_k,
        "packages": [record.to_jsonable() for record in records],
        "oak_boundary": {
            "review_only": True,
            "no_automatic_contact": True,
            "no_endorsement_claim": True,
            "human_review_required": True
        }
    }
    (out_dir / "publication_package_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_dashboard(records, out_dir)
    return records


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OAK-safe publication packages from a Tristan Publication Atlas manifest.")
    parser.add_argument("--atlas-manifest", default="artifacts/publication_atlas/publication_atlas_manifest.json")
    parser.add_argument("--templates", default="configs/tristan_publication_package_templates.json")
    parser.add_argument("--out-dir", default="artifacts/publication_packages")
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--top-k", type=int, default=50)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.top_k < 1:
        raise ValueError("--top-k must be >= 1")
    template_path = Path(args.templates) if args.templates else None
    records = build_packages(Path(args.atlas_manifest), template_path, Path(args.out_dir), args.min_score, args.top_k)
    print(json.dumps({
        "version": "omega.publication_package_factory.v1",
        "packages": len(records),
        "out_dir": args.out_dir,
        "min_score": args.min_score,
        "top_k": args.top_k,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
