#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Canadian University Research Harvester

Canada/Quebec research metadata atlas for AT-1 Accumulation Pure.

Purpose
-------
Harvest public scholarly metadata for major Quebec and Canadian universities,
convert the metadata into numeric tensors, and send each institutional bundle
through JKD -> FFWT/CVCD -> OAK.

Data source
-----------
Live mode uses OpenAlex public REST endpoints. Offline mode uses deterministic
synthetic metadata proxies so tests and local accumulation remain zero-key and
zero-network.

OAK guard
---------
This is bibliometric metadata triage. It is not a ranking, not a claim that all
best research has been captured, and not an evaluation of researchers. OpenAlex
affiliation metadata may be incomplete or noisy, so every live result is FERTILE
until downstream manual or multi-source validation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import argparse
import json
import math
import sys
import time
import urllib.parse
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from jkd_fusion_strike import jkd_strike  # noqa: E402

REPORT_PATH = ROOT / "reports" / "canada_research" / "canadian_university_research_report.json"
DEFAULT_WORKS_PER_INSTITUTION = 8
TENSOR_LENGTH = 512


@dataclass(frozen=True)
class InstitutionSeed:
    name: str
    province: str
    region: str
    priority: str


INSTITUTIONS: List[InstitutionSeed] = [
    # Quebec
    InstitutionSeed("Université de Montréal", "QC", "Quebec", "P0"),
    InstitutionSeed("McGill University", "QC", "Quebec", "P0"),
    InstitutionSeed("Université Laval", "QC", "Quebec", "P0"),
    InstitutionSeed("Université de Sherbrooke", "QC", "Quebec", "P0"),
    InstitutionSeed("Concordia University", "QC", "Quebec", "P0"),
    InstitutionSeed("École Polytechnique de Montréal", "QC", "Quebec", "P0"),
    InstitutionSeed("HEC Montréal", "QC", "Quebec", "P1"),
    InstitutionSeed("Université du Québec à Montréal", "QC", "Quebec", "P1"),
    InstitutionSeed("Institut national de la recherche scientifique", "QC", "Quebec", "P1"),
    InstitutionSeed("École de technologie supérieure", "QC", "Quebec", "P1"),
    # Canada-wide major research universities
    InstitutionSeed("University of Toronto", "ON", "Canada", "P0"),
    InstitutionSeed("University of British Columbia", "BC", "Canada", "P0"),
    InstitutionSeed("University of Alberta", "AB", "Canada", "P0"),
    InstitutionSeed("McMaster University", "ON", "Canada", "P0"),
    InstitutionSeed("University of Waterloo", "ON", "Canada", "P0"),
    InstitutionSeed("Western University", "ON", "Canada", "P1"),
    InstitutionSeed("University of Calgary", "AB", "Canada", "P1"),
    InstitutionSeed("University of Ottawa", "ON", "Canada", "P1"),
    InstitutionSeed("Queen's University", "ON", "Canada", "P1"),
    InstitutionSeed("Dalhousie University", "NS", "Canada", "P1"),
    InstitutionSeed("University of Manitoba", "MB", "Canada", "P1"),
    InstitutionSeed("University of Saskatchewan", "SK", "Canada", "P1"),
    InstitutionSeed("Simon Fraser University", "BC", "Canada", "P1"),
    InstitutionSeed("University of Victoria", "BC", "Canada", "P1"),
    InstitutionSeed("York University", "ON", "Canada", "P1"),
]


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rng_for(name: str) -> np.random.Generator:
    return np.random.default_rng(abs(hash((name, "CANADIAN-RESEARCH"))) % (2**32))


def fetch_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "TTM-CanadianResearchHarvester/0.1 (mailto:research@example.invalid)"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def openalex_institution(seed: InstitutionSeed) -> Optional[Dict[str, Any]]:
    query = urllib.parse.quote(seed.name)
    url = f"https://api.openalex.org/institutions?search={query}&filter=country_code:CA&per-page=3"
    data = fetch_json(url)
    results = data.get("results", [])
    if not results:
        return None
    # Prefer exact-ish display name; fallback to first result.
    lower = seed.name.lower()
    for item in results:
        if str(item.get("display_name", "")).lower() == lower:
            return item
    return results[0]


def openalex_works_for_institution(openalex_id: str, per_page: int) -> List[Dict[str, Any]]:
    encoded = urllib.parse.quote(openalex_id, safe=":/")
    filters = f"institutions.id:{encoded},from_publication_date:2020-01-01"
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
        "filter": filters,
        "sort": "cited_by_count:desc",
        "per-page": str(per_page),
    })
    data = fetch_json(url)
    return list(data.get("results", []))


def synthetic_works(seed: InstitutionSeed, count: int) -> List[Dict[str, Any]]:
    rng = rng_for(seed.name)
    families = ["materials", "ai", "health", "climate", "quantum", "social", "energy", "neuroscience"]
    works: List[Dict[str, Any]] = []
    base_year = 2020
    for idx in range(count):
        family = families[(idx + len(seed.name)) % len(families)]
        cited = int(max(0, rng.lognormal(mean=2.5, sigma=0.9)))
        year = base_year + int(idx % 6)
        title = f"{seed.name} synthetic {family} invariant study {idx + 1}"
        works.append({
            "id": f"synthetic:{seed.name}:{idx}",
            "title": title,
            "display_name": title,
            "publication_year": year,
            "cited_by_count": cited,
            "open_access": {"is_oa": bool(idx % 2 == 0)},
            "authorships": [{"author": {"display_name": f"Author {j}"}} for j in range(1 + idx % 7)],
            "topics": [{"display_name": family}],
            "primary_topic": {"display_name": family},
        })
    return works


def title_text(work: Dict[str, Any]) -> str:
    return str(work.get("title") or work.get("display_name") or "")


def work_features(work: Dict[str, Any]) -> List[float]:
    title = title_text(work)
    year = float(work.get("publication_year") or 0)
    cited = float(work.get("cited_by_count") or 0)
    oa = 1.0 if (work.get("open_access") or {}).get("is_oa") else 0.0
    authors = float(len(work.get("authorships") or []))
    topics = work.get("topics") or []
    topic_count = float(len(topics))
    title_len = float(len(title))
    ascii_energy = float(sum(ord(ch) for ch in title[:160]) / 1000.0)
    recency = max(0.0, year - 2000.0)
    return [recency, math.log1p(cited), oa, math.log1p(authors), math.log1p(topic_count), math.log1p(title_len), ascii_energy]


def works_to_tensor(works: List[Dict[str, Any]]) -> np.ndarray:
    values: List[float] = []
    for work in works:
        values.extend(work_features(work))
    if not values:
        values = [0.0]
    arr = np.asarray(values, dtype=float)
    if arr.size == 1:
        return np.full(TENSOR_LENGTH, float(arr[0]))
    source = np.linspace(0.0, 1.0, arr.size)
    target = np.linspace(0.0, 1.0, TENSOR_LENGTH)
    return np.interp(target, source, arr)


def compact_work(work: Dict[str, Any]) -> Dict[str, Any]:
    topic = (work.get("primary_topic") or {}).get("display_name")
    if not topic:
        topics = work.get("topics") or []
        topic = topics[0].get("display_name") if topics else None
    return {
        "id": work.get("id"),
        "title": title_text(work)[:300],
        "publication_year": work.get("publication_year"),
        "cited_by_count": work.get("cited_by_count"),
        "is_open_access": bool((work.get("open_access") or {}).get("is_oa")),
        "topic": topic,
        "doi": work.get("doi"),
    }


def compact_strike(tensor: np.ndarray, permutation_checks: int) -> Dict[str, Any]:
    result = jkd_strike(tensor, permutation_checks=permutation_checks)
    signatures = result.get("signatures_cvcd", {})
    control = result.get("permutation_control", {})
    return {
        "verdict": result.get("verdict"),
        "oak_score": result.get("oak_score"),
        "flattened_size": result.get("flattened_size"),
        "selected_invariants": {
            "fractal_ratio": signatures.get("fractal_ratio"),
            "ffwt_energy_entropy": signatures.get("ffwt_energy_entropy"),
            "ffwt_mean_adjacent_coherence": signatures.get("ffwt_mean_adjacent_coherence"),
            "ffwt_dominant_level": signatures.get("ffwt_dominant_level"),
            "ffwt_dominant_relative_energy": signatures.get("ffwt_dominant_relative_energy"),
            "null_z_score": control.get("null_z_score"),
            "null_percentile": control.get("null_percentile"),
            "used_permutations": control.get("used_permutations"),
        },
    }


def harvest_institution(seed: InstitutionSeed, live: bool, works_per_institution: int, permutation_checks: int) -> Dict[str, Any]:
    source = "offline:synthetic_openalex_like_metadata"
    institution_meta: Dict[str, Any] = {"display_name": seed.name, "id": None}
    works: List[Dict[str, Any]]
    error: Optional[str] = None
    if live:
        try:
            inst = openalex_institution(seed)
            if inst:
                institution_meta = {
                    "display_name": inst.get("display_name"),
                    "id": inst.get("id"),
                    "ror": inst.get("ror"),
                    "works_count": inst.get("works_count"),
                    "cited_by_count": inst.get("cited_by_count"),
                }
                works = openalex_works_for_institution(str(inst.get("id")), works_per_institution)
                source = "live:openalex"
            else:
                works = synthetic_works(seed, works_per_institution)
                source = "fallback:no_openalex_institution_match"
        except Exception as exc:
            works = synthetic_works(seed, works_per_institution)
            source = "fallback:openalex_error"
            error = str(exc)[:500]
    else:
        works = synthetic_works(seed, works_per_institution)

    tensor = works_to_tensor(works)
    strike = compact_strike(tensor, permutation_checks)
    return {
        "seed": asdict(seed),
        "source": source,
        "error": error,
        "institution": institution_meta,
        "works": [compact_work(w) for w in works[:works_per_institution]],
        "work_count": len(works),
        "metadata_tensor_features": ["recency", "log_citations", "open_access", "log_authors", "log_topics", "log_title_length", "title_ascii_energy"],
        "strike": strike,
    }


def load_history() -> Dict[str, Any]:
    if not REPORT_PATH.exists():
        return {"system": "TTM Canadian University Research Harvester", "runs": []}
    try:
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "runs" in data:
            return data
    except Exception:
        pass
    return {"system": "TTM Canadian University Research Harvester", "runs": []}


def summarize(institutions: Dict[str, Any]) -> Dict[str, Any]:
    provinces: Dict[str, int] = {}
    verdicts: Dict[str, int] = {}
    live_count = 0
    for payload in institutions.values():
        province = payload["seed"]["province"]
        provinces[province] = provinces.get(province, 0) + 1
        verdict = str(payload.get("strike", {}).get("verdict", "UNKNOWN"))
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
        if str(payload.get("source", "")).startswith("live:"):
            live_count += 1
    return {
        "institution_count": len(institutions),
        "province_counts": provinces,
        "verdict_counts": verdicts,
        "live_institution_count": live_count,
    }


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Harvest Canadian/Quebec university research metadata into JKD/OAK tensors")
    parser.add_argument("--live", action="store_true", help="query OpenAlex public API")
    parser.add_argument("--works-per-institution", type=int, default=DEFAULT_WORKS_PER_INSTITUTION)
    parser.add_argument("--permutation-checks", type=int, default=4)
    parser.add_argument("--priority", choices=["all", "P0", "P1"], default="all")
    args = parser.parse_args(argv)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    selected = [seed for seed in INSTITUTIONS if args.priority == "all" or seed.priority == args.priority]
    institutions = {
        seed.name: harvest_institution(seed, args.live, int(args.works_per_institution), int(args.permutation_checks))
        for seed in selected
    }
    run = {
        "timestamp": stamp(),
        "live_requested": bool(args.live),
        "works_per_institution": int(args.works_per_institution),
        "permutation_checks": int(args.permutation_checks),
        "summary": summarize(institutions),
        "institutions": institutions,
        "guard": "Metadata triage only; OpenAlex affiliation metadata can be incomplete/noisy; candidates require multi-source OAK validation.",
    }
    history = load_history()
    history.setdefault("runs", []).append(run)
    history["last_run"] = run
    REPORT_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(run["summary"], indent=2, ensure_ascii=False, sort_keys=True))
    return run


if __name__ == "__main__":
    main()
