#!/usr/bin/env python3
"""
Omega Open Data Harvester.

Stdlib-only, OAK-safe search and bounded download engine for open data sources.

Boundary:
- This engine searches metadata and downloads only explicitly linked files.
- It does not certify scientific truth, dataset quality, or license completeness.
- It always writes a manifest with source, query, license hints, size, status, and residues.
- Downloads are bounded by max_results and max_bytes_per_file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from xml.etree import ElementTree


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "omega.open_data_harvester.config.v1",
    "allowed_license_tokens": [
        "cc0", "cc-by", "cc-by-4.0", "cc-by-sa", "mit", "apache", "bsd", "public domain", "pddl"
    ],
    "default_sources": ["zenodo", "datacite", "openml", "rcsb", "arxiv"],
    "theories": {
        "omega_math_universe": {
            "queries": ["mathematical knowledge graph", "category theory dataset", "formal proof dataset"],
            "sources": ["zenodo", "datacite", "openml", "arxiv"]
        },
        "omega_spectro_universe": {
            "queries": ["open spectroscopy dataset", "Raman spectroscopy dataset", "FTIR spectroscopy dataset"],
            "sources": ["zenodo", "datacite", "openml", "arxiv"]
        },
        "omega_materials": {
            "queries": ["materials science dataset", "crystal structure dataset", "DFT dataset"],
            "sources": ["zenodo", "datacite", "openml", "arxiv"]
        },
        "ait_dynamics": {
            "queries": ["dynamical systems dataset", "PDE dataset", "time series benchmark"],
            "sources": ["zenodo", "datacite", "openml", "arxiv"]
        },
        "bayes_tristan": {
            "queries": ["Bayesian inference dataset", "uncertainty quantification benchmark", "probabilistic model dataset"],
            "sources": ["zenodo", "datacite", "openml", "arxiv"]
        },
        "hgfm": {
            "queries": ["graph dataset", "knowledge graph dataset", "hypergraph dataset"],
            "sources": ["zenodo", "datacite", "openml", "arxiv"]
        },
        "bio_hgfm": {
            "queries": ["protein structure", "molecular graph dataset", "bioinformatics graph dataset"],
            "sources": ["rcsb", "zenodo", "datacite", "openml", "arxiv"]
        }
    }
}


@dataclass
class DataItem:
    source: str
    query: str
    title: str
    url: str
    landing_url: str = ""
    download_url: str = ""
    license_hint: str = "unknown"
    size_bytes: int = 0
    item_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    residues: List[str] = field(default_factory=list)
    status: str = "metadata_only"

    def stable_id(self) -> str:
        payload = "||".join([self.source, self.query, self.title, self.url, self.download_url])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]

    def to_jsonable(self) -> Dict[str, Any]:
        data = self.__dict__.copy()
        data["stable_id"] = self.stable_id()
        return data


@dataclass
class HarvestTrace:
    version: str = "omega.open_data_harvest.v1"
    created_unix: float = field(default_factory=time.time)
    mode: str = "search"
    theory: str = "all"
    results: List[DataItem] = field(default_factory=list)
    downloads: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    residues: List[str] = field(default_factory=list)

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_unix": self.created_unix,
            "mode": self.mode,
            "theory": self.theory,
            "result_count": len(self.results),
            "download_count": len(self.downloads),
            "results": [item.to_jsonable() for item in self.results],
            "downloads": self.downloads,
            "errors": self.errors,
            "residues": self.residues,
            "oak_boundary": {
                "metadata_is_not_validation": True,
                "download_is_not_license_certification": True,
                "open_hint_requires_human_review": True,
                "scientific_claims_require_downstream_oak": True
            }
        }


def user_agent() -> str:
    return "OmegaOpenDataHarvester/1.0 (+https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2)"


def http_json(url: str, *, method: str = "GET", body: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
    data = None
    headers = {"User-Agent": user_agent(), "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def http_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent()})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def safe_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name.strip())
    name = re.sub(r"_+", "_", name).strip("._")
    return (name or "item")[:max_len]


def license_allowed(license_hint: str, tokens: Iterable[str]) -> bool:
    hint = (license_hint or "").lower()
    return any(token.lower() in hint for token in tokens)


def search_zenodo(query: str, max_results: int) -> List[DataItem]:
    url = "https://zenodo.org/api/records?" + urllib.parse.urlencode({"q": query, "size": str(max_results)})
    data = http_json(url)
    items: List[DataItem] = []
    for hit in data.get("hits", {}).get("hits", []):
        meta = hit.get("metadata", {})
        title = meta.get("title", "Zenodo record")
        license_hint = "unknown"
        license_obj = meta.get("license") or {}
        if isinstance(license_obj, dict):
            license_hint = license_obj.get("id") or license_obj.get("title") or "unknown"
        files = hit.get("files", []) or []
        first_file = files[0] if files else {}
        links = first_file.get("links", {}) if isinstance(first_file, dict) else {}
        download_url = links.get("self", "")
        size = int(first_file.get("size", 0) or 0) if isinstance(first_file, dict) else 0
        items.append(DataItem(
            source="zenodo",
            query=query,
            title=title,
            url=hit.get("links", {}).get("self", url),
            landing_url=hit.get("links", {}).get("html", ""),
            download_url=download_url,
            license_hint=license_hint,
            size_bytes=size,
            item_id=str(hit.get("id", "")),
            metadata={"created": hit.get("created"), "modified": hit.get("modified"), "doi": hit.get("doi")},
            residues=[] if download_url else ["no_download_url"],
        ))
    return items


def search_datacite(query: str, max_results: int) -> List[DataItem]:
    url = "https://api.datacite.org/dois?" + urllib.parse.urlencode({"query": query, "page[size]": str(max_results)})
    data = http_json(url)
    items: List[DataItem] = []
    for record in data.get("data", []):
        attrs = record.get("attributes", {})
        titles = attrs.get("titles") or []
        title = titles[0].get("title", "DataCite record") if titles else "DataCite record"
        rights = attrs.get("rightsList") or []
        license_hint = rights[0].get("rights", "unknown") if rights else "unknown"
        landing = attrs.get("url") or ""
        items.append(DataItem(
            source="datacite",
            query=query,
            title=title,
            url=record.get("links", {}).get("self", url),
            landing_url=landing,
            download_url="",
            license_hint=license_hint,
            item_id=record.get("id", ""),
            metadata={"doi": attrs.get("doi"), "publisher": attrs.get("publisher"), "types": attrs.get("types")},
            residues=["metadata_source", "no_direct_download"],
        ))
    return items


def search_openml(query: str, max_results: int) -> List[DataItem]:
    encoded = urllib.parse.quote(query)
    url = f"https://www.openml.org/api/v1/json/data/list/data_name/{encoded}/limit/{max_results}"
    data = http_json(url)
    raw = data.get("data", {}).get("dataset", [])
    if isinstance(raw, dict):
        raw = [raw]
    items: List[DataItem] = []
    for ds in raw:
        did = str(ds.get("did", ""))
        file_id = str(ds.get("file_id", ""))
        name = ds.get("name", f"openml_{did}")
        license_hint = ds.get("licence", "unknown") or "unknown"
        download_url = f"https://www.openml.org/data/v1/download/{file_id}" if file_id else ""
        items.append(DataItem(
            source="openml",
            query=query,
            title=name,
            url=f"https://www.openml.org/d/{did}" if did else url,
            landing_url=f"https://www.openml.org/d/{did}" if did else "",
            download_url=download_url,
            license_hint=license_hint,
            item_id=did,
            metadata={"version": ds.get("version"), "format": ds.get("format"), "qualities": ds.get("qualities")},
            residues=[] if download_url else ["no_file_id"],
        ))
    return items


def search_rcsb(query: str, max_results: int) -> List[DataItem]:
    body = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": query}
        },
        "request_options": {"paginate": {"start": 0, "rows": max_results}},
        "return_type": "entry"
    }
    data = http_json("https://search.rcsb.org/rcsbsearch/v2/query", method="POST", body=body)
    items: List[DataItem] = []
    for entry in data.get("result_set", []):
        pdb_id = entry.get("identifier", "")
        if not pdb_id:
            continue
        items.append(DataItem(
            source="rcsb",
            query=query,
            title=f"RCSB PDB structure {pdb_id}",
            url=f"https://www.rcsb.org/structure/{pdb_id}",
            landing_url=f"https://www.rcsb.org/structure/{pdb_id}",
            download_url=f"https://files.rcsb.org/download/{pdb_id}.cif",
            license_hint="RCSB PDB usage policy / open structure data",
            size_bytes=0,
            item_id=pdb_id,
            metadata={"score": entry.get("score")},
            residues=["license_policy_requires_review"],
        ))
    return items


def search_arxiv(query: str, max_results: int) -> List[DataItem]:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": "all:" + query, "start": "0", "max_results": str(max_results)})
    text = http_text(url)
    root = ElementTree.fromstring(text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items: List[DataItem] = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="arXiv record", namespaces=ns) or "").split())
        entry_id = entry.findtext("atom:id", default="", namespaces=ns) or ""
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href", "")
        items.append(DataItem(
            source="arxiv",
            query=query,
            title=title,
            url=entry_id,
            landing_url=entry_id,
            download_url="",
            license_hint="arXiv metadata; article license varies",
            item_id=entry_id.rsplit("/", 1)[-1],
            metadata={"pdf_url": pdf_url, "updated": entry.findtext("atom:updated", default="", namespaces=ns)},
            residues=["paper_metadata_not_dataset", "license_varies", "download_disabled_by_default"],
        ))
    return items


SEARCHERS = {
    "zenodo": search_zenodo,
    "datacite": search_datacite,
    "openml": search_openml,
    "rcsb": search_rcsb,
    "arxiv": search_arxiv,
}


def collect_queries(config: Dict[str, Any], theory: str, explicit_query: Optional[str]) -> Dict[str, Dict[str, Any]]:
    theories = config.get("theories", {})
    if explicit_query:
        return {theory: {"queries": [explicit_query], "sources": config.get("default_sources", [])}}
    if theory == "all":
        return theories
    if theory not in theories:
        raise KeyError(f"Unknown theory/science key: {theory}")
    return {theory: theories[theory]}


def search_all(config: Dict[str, Any], theory: str, query: Optional[str], sources: List[str], max_results: int, trace: HarvestTrace) -> List[DataItem]:
    plan = collect_queries(config, theory, query)
    all_items: List[DataItem] = []
    for theory_key, spec in plan.items():
        spec_sources = sources if sources else list(spec.get("sources") or config.get("default_sources", []))
        for q in spec.get("queries", []):
            for source in spec_sources:
                if source not in SEARCHERS:
                    trace.errors.append({"source": source, "query": q, "error": "unknown_source"})
                    continue
                try:
                    found = SEARCHERS[source](q, max_results)
                    for item in found:
                        item.metadata["theory"] = theory_key
                    all_items.extend(found)
                except Exception as exc:  # network/API errors should not crash the full run
                    trace.errors.append({"source": source, "query": q, "error": repr(exc)})
    trace.results.extend(all_items)
    return all_items


def download_item(item: DataItem, out_dir: Path, allowed_tokens: List[str], max_bytes: int, dry_run: bool) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "stable_id": item.stable_id(),
        "source": item.source,
        "title": item.title,
        "download_url": item.download_url,
        "status": "skipped",
        "path": "",
        "bytes": 0,
        "residues": list(item.residues),
    }
    if not item.download_url:
        record["residues"].append("missing_download_url")
        return record
    if item.size_bytes and item.size_bytes > max_bytes:
        record["residues"].append("file_too_large")
        record["bytes"] = item.size_bytes
        return record
    if item.license_hint != "unknown" and not license_allowed(item.license_hint, allowed_tokens):
        record["residues"].append("license_not_allowlisted")
        return record

    parsed = urllib.parse.urlparse(item.download_url)
    extension = Path(parsed.path).suffix or ".data"
    name = safe_filename(f"{item.source}_{item.item_id or item.stable_id()}_{item.title}") + extension
    target = out_dir / item.source / name
    record["path"] = str(target)
    if dry_run:
        record["status"] = "dry_run"
        return record

    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(item.download_url, headers={"User-Agent": user_agent()})
    total = 0
    with urllib.request.urlopen(req, timeout=60) as response, target.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 128)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                handle.close()
                target.unlink(missing_ok=True)
                record["status"] = "skipped"
                record["bytes"] = total
                record["residues"].append("stream_exceeded_max_bytes")
                return record
            handle.write(chunk)
    record["status"] = "downloaded"
    record["bytes"] = total
    return record


def write_manifest(path: Path, trace: HarvestTrace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace.to_jsonable(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search and optionally download open-source/open-data artifacts for Tristan theories.")
    parser.add_argument("--config", default="configs/omega_open_data_sources.json")
    parser.add_argument("--theory", default="all")
    parser.add_argument("--query", default=None)
    parser.add_argument("--sources", default="", help="Comma-separated sources; default uses config per theory.")
    parser.add_argument("--mode", choices=["search", "download"], default="search")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--max-bytes-per-file", type=int, default=25_000_000)
    parser.add_argument("--out-dir", default="artifacts/open_data")
    parser.add_argument("--manifest", default="artifacts/open_data/open_data_manifest.json")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def load_config(path: str) -> Dict[str, Any]:
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return DEFAULT_CONFIG


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.max_results < 1:
        raise ValueError("--max-results must be >= 1")
    if args.max_bytes_per_file < 1:
        raise ValueError("--max-bytes-per-file must be >= 1")

    config = load_config(args.config)
    selected_sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    trace = HarvestTrace(mode=args.mode, theory=args.theory)
    items = search_all(config, args.theory, args.query, selected_sources, args.max_results, trace)

    if args.mode == "download":
        allowed_tokens = list(config.get("allowed_license_tokens", []))
        out_dir = Path(args.out_dir)
        for item in items:
            try:
                trace.downloads.append(download_item(item, out_dir, allowed_tokens, args.max_bytes_per_file, args.dry_run))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                trace.errors.append({"source": item.source, "title": item.title, "error": repr(exc)})

    if not items:
        trace.residues.append("no_results_found")
    write_manifest(Path(args.manifest), trace)
    print(json.dumps({
        "version": trace.version,
        "mode": args.mode,
        "theory": args.theory,
        "results": len(trace.results),
        "downloads": len([d for d in trace.downloads if d.get("status") == "downloaded"]),
        "errors": len(trace.errors),
        "manifest": args.manifest,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
