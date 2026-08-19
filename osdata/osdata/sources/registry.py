from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class SourceSpec:
    id: str
    name: str
    category: str
    base_url: str
    access_mode: str
    license_hint: str
    citation_required: bool = True
    rate_limit_hint: str = 'respect provider limits'
    allowed: bool = True
    notes: str = ''
    def to_dict(self):
        return asdict(self)


def default_sources():
    return [
        SourceSpec('openalex', 'OpenAlex', 'science_metadata', 'https://api.openalex.org', 'REST API + snapshot', 'CC0 dataset / cite OpenAlex paper', True, 'free key and quota/cost limits apply', True, 'Works, authors, institutions, topics.'),
        SourceSpec('crossref', 'Crossref', 'doi_metadata', 'https://api.crossref.org', 'REST API', 'metadata terms/provider etiquette', True, 'use polite client and respect rate limits', True, 'DOI metadata and references.'),
        SourceSpec('arxiv', 'arXiv', 'preprints', 'https://export.arxiv.org/api/query', 'API', 'article licenses vary', True, 'respect provider etiquette', True, 'Preprints; license per paper.'),
        SourceSpec('huggingface_datasets', 'Hugging Face Datasets', 'ml_datasets', 'https://huggingface.co/datasets', 'Hub repositories/API', 'dataset-specific license', True, 'respect Hub rate limits and dataset cards', True, 'Community datasets; license must be checked per dataset.'),
        SourceSpec('github_public', 'GitHub Public Repositories', 'source_code', 'https://api.github.com', 'REST API', 'repository-specific license', True, 'respect GitHub API limits', True, 'Use only public repos and explicit licenses.'),
        SourceSpec('worldbank', 'World Bank Open Data', 'development_indicators', 'https://api.worldbank.org/v2', 'REST API', 'World Bank terms / open data', True, 'respect developer docs', True, 'Country, indicator, topic and metadata APIs.'),
        SourceSpec('owid', 'Our World in Data', 'public_statistics', 'https://ourworldindata.org', 'CSV/GitHub/data catalog', 'OWID license varies by dataset', True, 'respect dataset metadata', True, 'Public statistical datasets.'),
        SourceSpec('wikidata', 'Wikidata', 'knowledge_graph', 'https://query.wikidata.org', 'SPARQL/API dumps', 'CC0 for Wikidata content', True, 'respect query service limits', True, 'Linked open data graph.'),
    ]
