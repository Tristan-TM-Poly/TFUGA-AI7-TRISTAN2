from __future__ import annotations

import json
import urllib.parse

from omega_oss_digest_t.api_layer import (
    CachedHttpClient,
    GitHubApiClient,
    GitHubSearchIntent,
    StackExchangeApiClient,
    compile_github_repository_query,
    compile_stackoverflow_query,
    local_dependency_inventory,
    scan_text_for_secrets,
)


def test_github_query_compiler_quotes_and_qualifies():
    q = compile_github_repository_query(GitHubSearchIntent(
        keywords=("heat equation", "finite difference"),
        language="Python",
        license="mit",
        min_stars=50,
        pushed_after="2024-01-01",
    ))
    assert '"heat equation"' in q
    assert "language:Python" in q
    assert "license:mit" in q
    assert "stars:>=50" in q
    assert "pushed:>2024-01-01" in q


def test_stackoverflow_query_compiler_tags():
    q = compile_stackoverflow_query(("numpy broadcasting",), ("python", "numpy"))
    assert q["q"] == "numpy broadcasting"
    assert q["tagged"] == "python;numpy"


def test_secret_scanner_detects_github_token():
    findings = scan_text_for_secrets("TOKEN = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'\n")
    assert findings
    assert findings[0].kind == "github_token"


def test_dependency_inventory_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies=["requests>=2"]\n', encoding="utf-8")
    inv = local_dependency_inventory(tmp_path)
    assert inv["pyproject.toml"] == ["requests>=2"]


def test_github_api_uses_search_endpoint(tmp_path):
    seen = {}

    def fake_transport(request, timeout):
        seen["url"] = request.full_url
        body = {"items": [{"full_name": "octo/repo", "html_url": "https://github.com/octo/repo", "license": {"spdx_id": "MIT"}}]}
        return 200, {"etag": "abc", "x-ratelimit-remaining": "4999"}, json.dumps(body).encode()

    http = CachedHttpClient(cache_dir=tmp_path, transport=fake_transport, min_interval_seconds=0)
    client = GitHubApiClient(http=http, token="test")
    out = client.search_repositories(GitHubSearchIntent(keywords=("test",)), per_page=1)
    parsed = urllib.parse.urlparse(seen["url"])
    assert parsed.path == "/search/repositories"
    assert out[0].full_name == "octo/repo"
    assert out[0].license_id == "MIT"


def test_stackexchange_api_uses_advanced_search(tmp_path):
    seen = {}

    def fake_transport(request, timeout):
        seen["url"] = request.full_url
        body = {"items": [{"question_id": 1, "title": "T", "link": "https://stackoverflow.com/q/1", "creation_date": 1600000000, "tags": ["python"], "score": 3, "answer_count": 1, "is_answered": True}]}
        return 200, {}, json.dumps(body).encode()

    http = CachedHttpClient(cache_dir=tmp_path, transport=fake_transport, min_interval_seconds=0)
    client = StackExchangeApiClient(http=http)
    out = client.search_advanced(("error",), tags=("python",), pagesize=1)
    parsed = urllib.parse.urlparse(seen["url"])
    assert parsed.path.endswith("/search/advanced")
    assert out[0].question_id == 1
