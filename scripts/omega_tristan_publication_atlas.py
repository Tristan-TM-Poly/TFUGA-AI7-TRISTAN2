#!/usr/bin/env python3
"""
Omega Tristan Publication Atlas.

Stdlib-only, OAK-safe public metadata mapper for matching Tristan publication
projects to Canadian / Quebec universities, public authors, and research works.

Boundary:
- Uses public scholarly metadata only; no private data and no email automation.
- Produces publication dossiers and manifests, not outreach campaigns.
- Matches are heuristic and require human review before submission/contact.
- Research metadata is not proof of expertise, endorsement, or collaboration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "omega.tristan_publication_atlas.config.v1",
    "scopes": {
        "quebec": {
            "country_code": "CA",
            "institution_queries": [
                "McGill University",
                "Universite de Montreal",
                "Universite Laval",
                "Universite de Sherbrooke",
                "Concordia University",
                "Universite du Quebec a Montreal",
                "Polytechnique Montreal",
                "Ecole de technologie superieure",
                "HEC Montreal",
                "INRS",
                "Bishop's University",
                "Universite du Quebec a Trois-Rivieres",
                "Universite du Quebec a Chicoutimi",
                "Universite du Quebec a Rimouski",
                "Universite du Quebec en Outaouais",
                "Universite du Quebec en Abitibi-Temiscamingue",
                "TELUQ"
            ]
        },
        "canada": {
            "country_code": "CA",
            "institution_queries": [
                "university Canada",
                "polytechnic Canada",
                "institute technology Canada",
                "college university Canada"
            ]
        }
    },
    "tristan_projects": {
        "omega_math_universe": {
            "title": "Omega Math Universe",
            "keywords": ["mathematics", "category theory", "logic", "proof", "information theory", "graph theory", "topology"]
        },
        "omega_spectro_universe": {
            "title": "Omega Spectro Universe",
            "keywords": ["spectroscopy", "Raman", "FTIR", "NMR", "signal processing", "materials", "crystal"]
        },
        "omega_materials": {
            "title": "Omega Materials",
            "keywords": ["materials science", "solid state", "DFT", "crystal structure", "condensed matter"]
        },
        "ait_dynamics": {
            "title": "AIT Dynamics",
            "keywords": ["dynamical systems", "PDE", "SPDE", "time series", "chaos", "differential equations"]
        },
        "bayes_tristan": {
            "title": "Bayes-Tristan",
            "keywords": ["Bayesian", "uncertainty", "probabilistic", "causal inference", "decision theory"]
        },
        "hgfm": {
            "title": "Hypergraph Fractal Mycelial Framework",
            "keywords": ["hypergraph", "network science", "knowledge graph", "complex systems", "fractal"]
        },
        "ait_code_science": {
            "title": "AIT Math-to-Code Science Engine",
            "keywords": ["scientific computing", "symbolic computation", "code generation", "machine learning", "optimization"]
        }
    },
    "publication_outputs": [
        "concept_note",
        "paper_outline",
        "dataset_plan",
        "prototype_plan",
        "oak_validation_plan"
    ]
}


@dataclass
class Institution:
    openalex_id: str
    display_name: str
    country_code: str = ""
    city: str = ""
    region: str = ""
    works_count: int = 0
    cited_by_count: int = 0
    homepage_url: str = ""

    def slug(self) -> str:
        return safe_slug(self.display_name or self.openalex_id)


@dataclass
class PublicAuthor:
    openalex_id: str
    display_name: str
    works_count: int = 0
    cited_by_count: int = 0
    last_known_institution: str = ""
    concepts: List[str] = field(default_factory=list)

    def slug(self) -> str:
        return safe_slug(self.display_name or self.openalex_id)


@dataclass
class Work:
    openalex_id: str
    title: str
    publication_year: int = 0
    doi: str = ""
    landing_url: str = ""
    cited_by_count: int = 0
    authors: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)


@dataclass
class MatchCard:
    institution: Institution
    author: Optional[PublicAuthor]
    project_key: str
    project_title: str
    score: float
    matched_terms: List[str]
    works: List[Work]
    residues: List[str] = field(default_factory=list)

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "institution": self.institution.__dict__,
            "author": self.author.__dict__ if self.author else None,
            "project_key": self.project_key,
            "project_title": self.project_title,
            "score": self.score,
            "matched_terms": self.matched_terms,
            "works": [work.__dict__ for work in self.works],
            "residues": self.residues,
        }


@dataclass
class AtlasTrace:
    version: str = "omega.tristan_publication_atlas.v1"
    created_unix: float = field(default_factory=time.time)
    scope: str = "quebec"
    mode: str = "atlas"
    institutions: List[Institution] = field(default_factory=list)
    matches: List[MatchCard] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    residues: List[str] = field(default_factory=list)

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_unix": self.created_unix,
            "scope": self.scope,
            "mode": self.mode,
            "institution_count": len(self.institutions),
            "match_count": len(self.matches),
            "institutions": [inst.__dict__ for inst in self.institutions],
            "matches": [match.to_jsonable() for match in self.matches],
            "errors": self.errors,
            "residues": self.residues,
            "oak_boundary": {
                "public_metadata_only": True,
                "no_email_automation": True,
                "match_is_not_endorsement": True,
                "human_review_required": True,
                "submission_requires_professor_and_journal_specific_review": True
            }
        }


def safe_slug(text: str) -> str:
    text = text.strip().replace("'", "")
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower() or "item"


def stable_id(*parts: str, length: int = 16) -> str:
    return hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()[:length]


def user_agent() -> str:
    return "OmegaTristanPublicationAtlas/1.0 (+https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2)"


def http_json(url: str, timeout: int = 40) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent(), "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def openalex_url(entity: str, params: Dict[str, str]) -> str:
    return f"https://api.openalex.org/{entity}?" + urllib.parse.urlencode(params)


def normalize_openalex_id(value: str) -> str:
    if not value:
        return ""
    return value.rstrip("/").rsplit("/", 1)[-1]


def load_config(path: str) -> Dict[str, Any]:
    if Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return DEFAULT_CONFIG


def parse_institution(raw: Dict[str, Any]) -> Institution:
    geo = raw.get("geo") or {}
    return Institution(
        openalex_id=normalize_openalex_id(raw.get("id", "")),
        display_name=raw.get("display_name", ""),
        country_code=raw.get("country_code", ""),
        city=geo.get("city", "") or "",
        region=geo.get("region", "") or "",
        works_count=int(raw.get("works_count", 0) or 0),
        cited_by_count=int(raw.get("cited_by_count", 0) or 0),
        homepage_url=raw.get("homepage_url", "") or "",
    )


def search_institutions(query: str, country_code: str, max_institutions: int) -> List[Institution]:
    url = openalex_url("institutions", {
        "search": query,
        "filter": f"country_code:{country_code}",
        "per-page": str(max_institutions),
    })
    data = http_json(url)
    return [parse_institution(item) for item in data.get("results", [])]


def discover_institutions(config: Dict[str, Any], scope: str, max_institutions: int, offline: bool, trace: AtlasTrace) -> List[Institution]:
    scope_cfg = config.get("scopes", {}).get(scope)
    if not scope_cfg:
        raise KeyError(f"Unknown scope: {scope}")
    if offline:
        institutions = []
        for query in scope_cfg.get("institution_queries", [])[:max_institutions]:
            institutions.append(Institution(
                openalex_id="offline_" + stable_id(scope, query),
                display_name=query,
                country_code=scope_cfg.get("country_code", "CA"),
                region="offline_seed",
            ))
        return institutions

    seen: Dict[str, Institution] = {}
    for query in scope_cfg.get("institution_queries", []):
        try:
            for inst in search_institutions(query, scope_cfg.get("country_code", "CA"), max_institutions):
                if inst.openalex_id:
                    seen[inst.openalex_id] = inst
        except Exception as exc:
            trace.errors.append({"stage": "institution_search", "query": query, "error": repr(exc)})
    return list(seen.values())[:max_institutions]


def parse_author(raw: Dict[str, Any]) -> PublicAuthor:
    concepts = [c.get("display_name", "") for c in raw.get("x_concepts", [])[:8] if c.get("display_name")]
    inst = raw.get("last_known_institution") or {}
    return PublicAuthor(
        openalex_id=normalize_openalex_id(raw.get("id", "")),
        display_name=raw.get("display_name", ""),
        works_count=int(raw.get("works_count", 0) or 0),
        cited_by_count=int(raw.get("cited_by_count", 0) or 0),
        last_known_institution=inst.get("display_name", "") if isinstance(inst, dict) else "",
        concepts=concepts,
    )


def search_authors(institution: Institution, query: str, max_authors: int) -> List[PublicAuthor]:
    if not institution.openalex_id or institution.openalex_id.startswith("offline_"):
        return []
    filt = f"last_known_institution.id:{institution.openalex_id}"
    url = openalex_url("authors", {"filter": filt, "search": query, "per-page": str(max_authors)})
    data = http_json(url)
    return [parse_author(item) for item in data.get("results", [])]


def parse_work(raw: Dict[str, Any]) -> Work:
    authorships = raw.get("authorships") or []
    authors = []
    for authorship in authorships[:8]:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)
    concepts = [c.get("display_name", "") for c in raw.get("concepts", [])[:8] if c.get("display_name")]
    primary = raw.get("primary_location") or {}
    source = primary.get("source") or {}
    return Work(
        openalex_id=normalize_openalex_id(raw.get("id", "")),
        title=raw.get("title", "") or "Untitled work",
        publication_year=int(raw.get("publication_year", 0) or 0),
        doi=raw.get("doi", "") or "",
        landing_url=raw.get("doi", "") or raw.get("id", "") or source.get("homepage_url", ""),
        cited_by_count=int(raw.get("cited_by_count", 0) or 0),
        authors=authors,
        concepts=concepts,
    )


def search_works_for_author(author: PublicAuthor, query: str, max_works: int) -> List[Work]:
    if not author.openalex_id:
        return []
    filt = f"authorships.author.id:{author.openalex_id}"
    url = openalex_url("works", {"filter": filt, "search": query, "per-page": str(max_works), "sort": "cited_by_count:desc"})
    data = http_json(url)
    return [parse_work(item) for item in data.get("results", [])]


def search_works_for_institution(institution: Institution, query: str, max_works: int) -> List[Work]:
    if not institution.openalex_id or institution.openalex_id.startswith("offline_"):
        return []
    filt = f"institutions.id:{institution.openalex_id}"
    url = openalex_url("works", {"filter": filt, "search": query, "per-page": str(max_works), "sort": "cited_by_count:desc"})
    data = http_json(url)
    return [parse_work(item) for item in data.get("results", [])]


def score_match(project_keywords: Iterable[str], author: Optional[PublicAuthor], works: List[Work]) -> Tuple[float, List[str]]:
    keywords = [k.lower() for k in project_keywords]
    haystack_parts: List[str] = []
    if author:
        haystack_parts.extend(author.concepts)
    for work in works:
        haystack_parts.append(work.title)
        haystack_parts.extend(work.concepts)
    haystack = " ".join(haystack_parts).lower()
    matched = [kw for kw in keywords if kw.lower() in haystack]
    citation_signal = sum(min(work.cited_by_count, 50) for work in works) / 50.0
    author_signal = min((author.works_count if author else len(works)) / 20.0, 2.0)
    score = len(matched) * 2.0 + citation_signal + author_signal
    return round(score, 3), matched


def build_atlas(config: Dict[str, Any], scope: str, max_institutions: int, max_authors: int, max_works: int, offline: bool, trace: AtlasTrace) -> AtlasTrace:
    institutions = discover_institutions(config, scope, max_institutions, offline, trace)
    trace.institutions.extend(institutions)
    projects = config.get("tristan_projects", {})

    for institution in institutions:
        if offline:
            for project_key, project in projects.items():
                trace.matches.append(MatchCard(
                    institution=institution,
                    author=None,
                    project_key=project_key,
                    project_title=project.get("title", project_key),
                    score=0.0,
                    matched_terms=[],
                    works=[],
                    residues=["offline_template", "no_public_metadata_fetched"],
                ))
            continue

        for project_key, project in projects.items():
            keywords = project.get("keywords", [])
            author_query = " ".join(keywords[:3]) if keywords else project_key
            authors: List[PublicAuthor] = []
            try:
                authors = search_authors(institution, author_query, max_authors)
            except Exception as exc:
                trace.errors.append({"stage": "author_search", "institution": institution.display_name, "project": project_key, "error": repr(exc)})

            if not authors:
                try:
                    works = search_works_for_institution(institution, author_query, max_works)
                    score, matched = score_match(keywords, None, works)
                    trace.matches.append(MatchCard(
                        institution=institution,
                        author=None,
                        project_key=project_key,
                        project_title=project.get("title", project_key),
                        score=score,
                        matched_terms=matched,
                        works=works,
                        residues=["institution_level_match", "no_author_match"],
                    ))
                except Exception as exc:
                    trace.errors.append({"stage": "institution_work_search", "institution": institution.display_name, "project": project_key, "error": repr(exc)})
                continue

            for author in authors[:max_authors]:
                works: List[Work] = []
                try:
                    works = search_works_for_author(author, author_query, max_works)
                except Exception as exc:
                    trace.errors.append({"stage": "author_work_search", "author": author.display_name, "project": project_key, "error": repr(exc)})
                score, matched = score_match(keywords, author, works)
                trace.matches.append(MatchCard(
                    institution=institution,
                    author=author,
                    project_key=project_key,
                    project_title=project.get("title", project_key),
                    score=score,
                    matched_terms=matched,
                    works=works,
                    residues=[] if matched else ["weak_keyword_match"],
                ))
    if not trace.matches:
        trace.residues.append("no_matches_generated")
    return trace


def markdown_card(match: MatchCard) -> str:
    author_line = match.author.display_name if match.author else "Institution-level match"
    work_lines = []
    for work in match.works[:8]:
        link = work.landing_url or work.doi or work.openalex_id
        work_lines.append(f"- {work.publication_year}: {work.title} ({link})")
    if not work_lines:
        work_lines.append("- No works attached in this run.")
    return f"""# Tristan Publication Dossier: {match.project_title}

## Institution

{match.institution.display_name}

## Public author / research node

{author_line}

## Heuristic fit

- Score: {match.score}
- Matched terms: {', '.join(match.matched_terms) if match.matched_terms else 'none'}
- Residues: {', '.join(match.residues) if match.residues else 'none'}

## Relevant public works

{chr(10).join(work_lines)}

## Tristan publication package

- Concept note: frame `{match.project_title}` with OAK boundaries.
- Paper outline: problem, prior work, method, validation, residues.
- Dataset plan: open-data sources, licenses, reproducible manifests.
- Prototype plan: minimal executable artifact in the repo.
- OAK validation plan: falsification tests, negative memory, benchmark criteria.

## Boundary

This dossier is based on public metadata. It is not an endorsement, not an authorship claim, and not an email/contact action.
"""


def write_outputs(trace: AtlasTrace, out_dir: Path, top_k: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "publication_atlas_manifest.json").write_text(json.dumps(trace.to_jsonable(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ranked = sorted(trace.matches, key=lambda m: m.score, reverse=True)
    lines = ["# Tristan Publication Atlas", "", f"Scope: `{trace.scope}`", f"Matches: {len(trace.matches)}", "", "## Top matches", ""]
    for match in ranked[:top_k]:
        author = match.author.display_name if match.author else "institution-level"
        lines.append(f"- **{match.project_title}** × **{match.institution.display_name}** × `{author}` — score `{match.score}`")
    (out_dir / "PUBLICATION_ATLAS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dossiers = out_dir / "dossiers"
    for match in ranked[:top_k]:
        inst_slug = match.institution.slug()
        author_slug = match.author.slug() if match.author else "institution-level"
        path = dossiers / inst_slug / f"{safe_slug(match.project_key)}__{author_slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown_card(match), encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Tristan publication dossiers from public scholarly metadata.")
    parser.add_argument("--config", default="configs/tristan_publication_atlas.json")
    parser.add_argument("--scope", choices=["quebec", "canada"], default="quebec")
    parser.add_argument("--mode", choices=["atlas"], default="atlas")
    parser.add_argument("--max-institutions", type=int, default=20)
    parser.add_argument("--max-authors", type=int, default=3)
    parser.add_argument("--max-works", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--out-dir", default="artifacts/publication_atlas")
    parser.add_argument("--offline", action="store_true", help="Use config seed institutions only; no network calls.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.max_institutions < 1 or args.max_authors < 1 or args.max_works < 1:
        raise ValueError("max-institutions, max-authors, and max-works must be >= 1")
    config = load_config(args.config)
    trace = AtlasTrace(scope=args.scope, mode=args.mode)
    build_atlas(config, args.scope, args.max_institutions, args.max_authors, args.max_works, args.offline, trace)
    write_outputs(trace, Path(args.out_dir), args.top_k)
    print(json.dumps({
        "version": trace.version,
        "scope": trace.scope,
        "institutions": len(trace.institutions),
        "matches": len(trace.matches),
        "errors": len(trace.errors),
        "out_dir": args.out_dir,
        "offline": args.offline,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
