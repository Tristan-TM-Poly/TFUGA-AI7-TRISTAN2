from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import os
from typing import Any, Callable
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from .max_models import NormalizedRecord, canonical_json

Parser = Callable[[bytes, str], list[NormalizedRecord]]
UrlBuilder = Callable[[str, int, int, dict[str, str]], str]


@dataclass(frozen=True)
class Adapter:
    source_id: str
    name: str
    access_state: str
    required_env: tuple[str, ...]
    requests_per_second: float
    max_pages: int
    url_builder: UrlBuilder
    parser: Parser
    policy_url: str
    metadata_only: bool = True

    def missing_env(self, env: dict[str, str] | None = None) -> tuple[str, ...]:
        values = os.environ if env is None else env
        return tuple(key for key in self.required_env if not values.get(key))


def _payload_hash(item: object) -> str:
    return hashlib.sha256(canonical_json(item).encode("utf-8")).hexdigest()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        value = str(value).strip()
        return value or None
    return None


def _first(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return _text(value[0])
    return _text(value)


def _record(source_id: str, record_id: object, receipt_id: str, payload: object, **kwargs: Any) -> NormalizedRecord:
    return NormalizedRecord(
        source_id=source_id,
        record_id=str(record_id),
        request_receipt_id=receipt_id,
        source_payload_sha256=_payload_hash(payload),
        **kwargs,
    )


def parse_wikimedia(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    pages = payload.get("query", {}).get("pages", [])
    if isinstance(pages, dict):
        pages = list(pages.values())
    out = []
    for item in pages if isinstance(pages, list) else []:
        if not isinstance(item, dict):
            continue
        pageid = item.get("pageid") or item.get("title")
        if pageid is None:
            continue
        out.append(_record("wikimedia", pageid, receipt_id, item, title=_text(item.get("title")), canonical_url=_text(item.get("fullurl")), record_type="encyclopedia_page"))
    return out


def parse_crossref(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    items = payload.get("message", {}).get("items", [])
    out = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not item.get("DOI"):
            continue
        published = item.get("published", {}).get("date-parts")
        issued = None
        if isinstance(published, list) and published and isinstance(published[0], list):
            issued = "-".join(str(part) for part in published[0])
        license_value = None
        licenses = item.get("license")
        if isinstance(licenses, list) and licenses and isinstance(licenses[0], dict):
            license_value = _text(licenses[0].get("URL"))
        doi = str(item["DOI"])
        out.append(_record("crossref", doi, receipt_id, item, title=_first(item.get("title")), canonical_url=_text(item.get("URL")) or f"https://doi.org/{doi}", record_type=_text(item.get("type")), issued=issued, license=license_value, identifiers={"doi": doi}))
    return out


def parse_pubmed(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    ids = payload.get("esearchresult", {}).get("idlist", [])
    return [_record("pubmed", pmid, receipt_id, {"pmid": pmid}, canonical_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", record_type="pubmed_record", identifiers={"pmid": str(pmid)}) for pmid in ids if str(pmid).strip()]


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_pmc_oai(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    root = ET.fromstring(body)
    out: list[NormalizedRecord] = []
    for node in root.iter():
        if _local(node.tag) != "record":
            continue
        identifier = None
        datestamp = None
        title = None
        canonical_url = None
        rights = None
        record_type = "pmc_oai_record"
        identifiers: dict[str, str] = {}
        raw: dict[str, Any] = {}
        for child in node.iter():
            name = _local(child.tag)
            value = (child.text or "").strip()
            if not value:
                continue
            raw.setdefault(name, value)
            if name == "identifier" and identifier is None:
                identifier = value
            elif name == "datestamp":
                datestamp = value
            elif name == "title" and title is None:
                title = value
            elif name == "rights" and rights is None:
                rights = value
            elif name == "type" and record_type == "pmc_oai_record":
                record_type = value
            if name == "identifier":
                if "pmc" in value.lower():
                    identifiers.setdefault("pmc", value)
                if value.startswith("http"):
                    canonical_url = canonical_url or value
        if identifier:
            out.append(_record("pmc_open", identifier, receipt_id, raw, title=title, canonical_url=canonical_url, record_type=record_type, issued=datestamp, license=rights, identifiers=identifiers))
    return out


def _generic_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    candidates: list[Any] = [payload.get("results"), payload.get("records"), payload.get("data"), payload.get("items")]
    hits = payload.get("hits")
    if isinstance(hits, dict):
        candidates.extend([hits.get("hits"), hits.get("items")])
    for value in candidates:
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def parse_nist(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    out = []
    for item in _generic_items(payload):
        core = item.get("metadata") if isinstance(item.get("metadata"), dict) else item
        rid = core.get("id") or core.get("record_id") or core.get("doi") or item.get("id")
        if rid is None:
            continue
        doi = _text(core.get("doi"))
        out.append(_record("nist_pdr", rid, receipt_id, core, title=_first(core.get("title")), canonical_url=_text(core.get("url")) or _text(core.get("landingPage")), record_type=_text(core.get("type")) or "nist_resource", issued=_text(core.get("issued")) or _text(core.get("release_date")), updated=_text(core.get("modified")), license=_text(core.get("license")), identifiers={"doi": doi} if doi else {}))
    return out


def parse_nasa(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    items = payload if isinstance(payload, list) else [payload]
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rid = item.get("date") or item.get("url") or item.get("title")
        if rid is None:
            continue
        out.append(_record("nasa_open", rid, receipt_id, item, title=_text(item.get("title")), canonical_url=_text(item.get("url")), record_type=_text(item.get("media_type")) or "nasa_metadata", issued=_text(item.get("date"))))
    return out


def parse_cern(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    out = []
    for item in _generic_items(payload):
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else item
        rid = item.get("id") or metadata.get("recid") or metadata.get("id") or metadata.get("doi")
        if rid is None:
            continue
        doi = _text(metadata.get("doi"))
        lic = metadata.get("license")
        if isinstance(lic, dict):
            lic = lic.get("id") or lic.get("url")
        out.append(_record("cern_open_data", rid, receipt_id, metadata, title=_first(metadata.get("title")), canonical_url=_text(item.get("links", {}).get("self") if isinstance(item.get("links"), dict) else None), record_type=_text(metadata.get("type")) or "cern_record", issued=_text(metadata.get("date")) or _text(metadata.get("publication_date")), license=_text(lic), identifiers={"doi": doi} if doi else {}))
    return out


def parse_usgs(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    features = payload.get("features", []) if isinstance(payload, dict) else []
    out = []
    for item in features if isinstance(features, list) else []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        props = item.get("properties") if isinstance(item.get("properties"), dict) else {}
        out.append(_record("usgs", item["id"], receipt_id, item, title=_text(props.get("title")), canonical_url=_text(props.get("url")), record_type=_text(props.get("type")) or "earthquake_event", issued=_text(props.get("time")), updated=_text(props.get("updated")), topics=("earthquake",)))
    return out


def parse_canada(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    items = payload.get("result", {}).get("results", []) if isinstance(payload, dict) else []
    out = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        rid = item.get("id") or item.get("name")
        if rid is None:
            continue
        title = item.get("title_translated")
        if isinstance(title, dict):
            title = title.get("en") or title.get("fr")
        title = _text(title) or _text(item.get("title"))
        lic = item.get("license_title") or item.get("license_id")
        out.append(_record("canada_open", rid, receipt_id, item, title=title, canonical_url=_text(item.get("url")), record_type=_text(item.get("type")) or "open_government_dataset", issued=_text(item.get("metadata_created")), updated=_text(item.get("metadata_modified")), license=_text(lic), identifiers={"ckan_id": str(rid)}))
    return out


def parse_esa_description(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    root = ET.fromstring(body)
    values: dict[str, Any] = {}
    urls: list[str] = []
    for node in root.iter():
        name = _local(node.tag)
        text = (node.text or "").strip()
        if name in {"ShortName", "LongName", "Description", "Contact", "Tags"} and text:
            values[name] = text
        if name == "Url" and node.attrib.get("template"):
            urls.append(node.attrib["template"])
    values["templates"] = urls
    rid = values.get("ShortName") or "esa-cci-opensearch"
    return [_record("esa_cci", rid, receipt_id, values, title=_text(values.get("LongName")) or _text(values.get("ShortName")), canonical_url="https://archive.opensearch.ceda.ac.uk/opensearch/description.xml", record_type="opensearch_capability", topics=("climate", "earth_observation"))]


def parse_openalex(body: bytes, receipt_id: str) -> list[NormalizedRecord]:
    payload = json.loads(body)
    items = payload.get("results", []) if isinstance(payload, dict) else []
    out = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
        doi = _text(ids.get("doi"))
        out.append(_record("openalex", item["id"], receipt_id, item, title=_text(item.get("title")) or _text(item.get("display_name")), canonical_url=_text(item.get("id")), record_type=_text(item.get("type")) or "scholarly_work", issued=_text(item.get("publication_date")), updated=_text(item.get("updated_date")), identifiers={"doi": doi} if doi else {}))
    return out


def _qs(base: str, params: dict[str, object]) -> str:
    return base + "?" + urlencode(params, doseq=True)


def _wikimedia(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://en.wikipedia.org/w/api.php", {"action": "query", "generator": "search", "gsrsearch": query, "gsrlimit": min(size, 50), "gsroffset": (page - 1) * size, "prop": "info", "inprop": "url", "format": "json", "formatversion": 2, "maxlag": 1})


def _crossref(query: str, page: int, size: int, env: dict[str, str]) -> str:
    params: dict[str, object] = {"query.title": query, "rows": min(size, 100), "offset": (page - 1) * size, "select": "DOI,title,published,URL,type,license"}
    if env.get("CROSSREF_MAILTO"):
        params["mailto"] = env["CROSSREF_MAILTO"]
    return _qs("https://api.crossref.org/works", params)


def _pubmed(query: str, page: int, size: int, env: dict[str, str]) -> str:
    params: dict[str, object] = {"db": "pubmed", "term": query, "retmax": min(size, 100), "retstart": (page - 1) * size, "retmode": "json", "tool": "omega_web_hg_r04"}
    if env.get("NCBI_EMAIL"):
        params["email"] = env["NCBI_EMAIL"]
    if env.get("NCBI_API_KEY"):
        params["api_key"] = env["NCBI_API_KEY"]
    return _qs("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params)


def _pmc(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/", {"verb": "ListRecords", "metadataPrefix": "oai_dc"})


def _nist(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://data.nist.gov/rmm/records", {"search": query, "limit": min(size, 100), "offset": (page - 1) * size})


def _nasa(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://api.nasa.gov/planetary/apod", {"api_key": env["NASA_API_KEY"], "date": date.today().isoformat(), "thumbs": "false"})


def _cern(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://opendata.cern.ch/api/records/", {"q": query, "size": min(size, 100), "page": page})


def _usgs(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://earthquake.usgs.gov/fdsnws/event/1/query", {"format": "geojson", "limit": min(size, 100), "offset": (page - 1) * size + 1, "orderby": "time"})


def _esa(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return "https://archive.opensearch.ceda.ac.uk/opensearch/description.xml"


def _canada(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://open.canada.ca/data/api/action/package_search", {"q": query, "rows": min(size, 100), "start": (page - 1) * size})


def _openalex(query: str, page: int, size: int, env: dict[str, str]) -> str:
    return _qs("https://api.openalex.org/works", {"search": query, "per_page": min(size, 100), "page": page, "select": "id,title,type,publication_date,updated_date,ids", "api_key": env["OPENALEX_API_KEY"]})


MAX_ADAPTERS: tuple[Adapter, ...] = (
    Adapter("wikimedia", "Wikimedia", "ready", (), 1.0, 4, _wikimedia, parse_wikimedia, "https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy"),
    Adapter("crossref", "Crossref", "ready", (), 0.5, 4, _crossref, parse_crossref, "https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/"),
    Adapter("pubmed", "PubMed", "ready", (), 0.3, 4, _pubmed, parse_pubmed, "https://www.ncbi.nlm.nih.gov/books/NBK25497/"),
    Adapter("pmc_open", "PMC OAI", "ready", (), 0.2, 1, _pmc, parse_pmc_oai, "https://pmc.ncbi.nlm.nih.gov/tools/oai/"),
    Adapter("nist_pdr", "NIST PDR", "ready", (), 0.5, 3, _nist, parse_nist, "https://data.nist.gov/rmm/"),
    Adapter("nasa_open", "NASA Open APIs", "key_required", ("NASA_API_KEY",), 0.2, 1, _nasa, parse_nasa, "https://api.nasa.gov/"),
    Adapter("cern_open_data", "CERN Open Data", "ready", (), 0.3, 3, _cern, parse_cern, "https://opendata.cern.ch/docs/about"),
    Adapter("usgs", "USGS Earthquake Catalog", "ready", (), 0.2, 3, _usgs, parse_usgs, "https://earthquake.usgs.gov/fdsnws/event/1"),
    Adapter("esa_cci", "ESA CCI OpenSearch", "ready", (), 0.2, 1, _esa, parse_esa_description, "https://climate.esa.int/data/apis"),
    Adapter("canada_open", "Government of Canada Open Data", "ready", (), 0.5, 3, _canada, parse_canada, "https://open.canada.ca/en/working-data-api/best-practices"),
    Adapter("openalex", "OpenAlex", "key_required", ("OPENALEX_API_KEY",), 1.0, 4, _openalex, parse_openalex, "https://developers.openalex.org/api-reference/authentication"),
)


def adapter_by_id(source_id: str) -> Adapter:
    for adapter in MAX_ADAPTERS:
        if adapter.source_id == source_id:
            return adapter
    raise KeyError(source_id)
