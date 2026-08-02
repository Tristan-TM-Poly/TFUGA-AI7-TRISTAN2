from __future__ import annotations

import json

import pytest

from omega_wiki_t.core import CitationPreservingTranslator, WikiCompiler, invariant_tokens
from omega_wiki_t.cli import main


PAGES = {
    "fr": {
        "title": "Mécanique quantique",
        "canonicalurl": "https://fr.wikipedia.org/wiki/M%C3%A9canique_quantique",
        "pageprops": {"wikibase_item": "Q944"},
        "revisions": [{"revid": 101, "timestamp": "2026-01-01T00:00:00Z", "sha1": "frsha"}],
        "langlinks": [{"lang": "en", "title": "Quantum mechanics"}],
    },
    "en": {
        "title": "Quantum mechanics",
        "canonicalurl": "https://en.wikipedia.org/wiki/Quantum_mechanics",
        "pageprops": {"wikibase_item": "Q944"},
        "revisions": [{"revid": 202, "timestamp": "2026-01-02T00:00:00Z", "sha1": "ensha"}],
        "langlinks": [{"lang": "fr", "title": "Mécanique quantique"}],
    },
}

HTML = {
    "fr": """
        <h2>Principe</h2>
        <p>Une valeur mesurée vaut 300 K.<sup class="reference"><a href="#cite_note-1">[1]</a></sup></p>
        <ol class="references"><li><cite><a href="https://example.org/source-fr">Source</a></cite></li></ol>
    """,
    "en": """
        <h2>Principle</h2>
        <p>A measured value is 300 K.<sup class="reference"><a href="#cite_note-1">[1]</a></sup></p>
        <ol class="references"><li><cite><a href="https://example.org/source-en">Source</a></cite></li></ol>
    """,
}


class FakeClient:
    def __init__(self, language: str) -> None:
        self.language = language

    def resolve(self, title: str):
        return PAGES[self.language]

    def parse(self, title: str):
        return {
            "title": PAGES[self.language]["title"],
            "text": HTML[self.language],
            "sections": [{"line": "Principle"}],
            "externallinks": [f"https://example.org/source-{self.language}"],
            "langlinks": [],
            "revid": PAGES[self.language]["revisions"][0]["revid"],
        }


def test_compile_multilingual_bundle_is_deterministic(tmp_path):
    compiler = WikiCompiler(client_factory=FakeClient)
    first = compiler.compile("Mécanique quantique", source_language="fr", target_languages=["en"])
    second = compiler.compile("Mécanique quantique", source_language="fr", target_languages=["en"])

    assert first.qid == "Q944"
    assert [article.language for article in first.articles] == ["fr", "en"]
    assert [claim.claim_id for claim in first.claims] == [claim.claim_id for claim in second.claims]
    assert all(claim.citation_markers for claim in first.claims)

    output = compiler.write(first, tmp_path / "bundle")
    assert (output / "manifest.json").is_file()
    assert (output / "claims.jsonl").is_file()
    assert (output / "report.md").is_file()

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["article_count"] == 2
    assert manifest["oak_status"].startswith("R0.1_READ_ONLY")


def test_local_audit_detects_no_orphan_source_ids(tmp_path, capsys):
    compiler = WikiCompiler(client_factory=FakeClient)
    result = compiler.compile("Mécanique quantique", source_language="fr", target_languages=["en"])
    bundle = compiler.write(result, tmp_path / "bundle")

    exit_code = main(["audit", str(bundle)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "PASS_WITH_R0_1_LIMITS"
    assert payload["issues"] == []


def test_translation_guard_fails_closed_when_invariants_disappear():
    translator = CitationPreservingTranslator(lambda text, source, target: "La valeur est différente.")

    with pytest.raises(ValueError, match="lost invariants"):
        translator.translate("Value: 300 K on 2026-01-02 [REF:c1]", "en", "fr")


def test_translation_guard_accepts_preserved_invariants():
    translator = CitationPreservingTranslator(
        lambda text, source, target: "Valeur : 300 K le 2026-01-02 [REF:c1]"
    )
    translated = translator.translate("Value: 300 K on 2026-01-02 [REF:c1]", "en", "fr")

    assert invariant_tokens(translated) == invariant_tokens("Value: 300 K on 2026-01-02 [REF:c1]")
