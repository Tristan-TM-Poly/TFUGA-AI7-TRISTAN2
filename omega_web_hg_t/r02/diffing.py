from __future__ import annotations

import json
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def compare_run_directories(previous: str | Path, current: str | Path) -> dict[str, object]:
    old_root, new_root = Path(previous), Path(current)
    old_pages = {str(item["canonical_url"]): item for item in _read_jsonl(old_root / "pages.jsonl")}
    new_pages = {str(item["canonical_url"]): item for item in _read_jsonl(new_root / "pages.jsonl")}
    old_urls, new_urls = set(old_pages), set(new_pages)
    added = sorted(new_urls - old_urls)
    removed = sorted(old_urls - new_urls)
    modified = []
    unchanged = []
    for url in sorted(old_urls & new_urls):
        old_hash = old_pages[url].get("content_sha256")
        new_hash = new_pages[url].get("content_sha256")
        if old_hash == new_hash:
            unchanged.append(url)
        else:
            modified.append({"url": url, "previous_sha256": old_hash, "current_sha256": new_hash})
    return {
        "schema": "omega-web-hg-run-diff/0.2",
        "previous": str(old_root),
        "current": str(new_root),
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
        "counts": {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "unchanged": len(unchanged),
        },
    }
