"""Minimal live demo for Ω-WIKI-T∞.

This performs read-only Wikimedia requests. It does not fact-check the output.
"""

from omega_wiki_t import WikiCompiler


def main() -> None:
    compiler = WikiCompiler()
    result = compiler.compile(
        "Mécanique quantique",
        source_language="fr",
        target_languages=["en"],
    )
    output = compiler.write(result, "generated/omega_wiki_t_q944")
    print(f"Wrote {len(result.articles)} articles and {len(result.claims)} claim candidates to {output}")


if __name__ == "__main__":
    main()
