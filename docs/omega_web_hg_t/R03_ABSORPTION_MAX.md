# Ω-WEB-HG-T∞ R0.3 — Absorption probatoire et recherche

R0.3 est une couche **hors réseau** qui transforme un run R0.2 en corpus interrogeable sans détacher les textes de leurs pages, sections et preuves.

## Pipeline

```text
run R0.2
  → pages + sections + evidence
  → segmentation déterministe en phrases
  → claims candidats non vérifiés
  → SHA-256 + SimHash 64 bits
  → déduplication exacte et proche
  → hypergraphe section→claim→preuve
  → index SQLite / FTS5
  → requête → texte + URL + locator + evidence_id
  → audit OAK
```

## Commandes

```bash
omega-web-hg-r03 build <run-r02> \
  --output-dir generated/omega_web_hg_t_r03/corpus

omega-web-hg-r03 query generated/omega_web_hg_t_r03/corpus \
  "preuve reproductible" \
  --kind claim_candidate \
  --limit 20

omega-web-hg-r03 audit generated/omega_web_hg_t_r03/corpus
```

## Sorties

```text
manifest.json
claim-candidates.jsonl
duplicates.jsonl
absorption-hypergraph.json
absorption-report.json
search.sqlite3
```

## Déduplication sans plafond total arbitraire

La déduplication exacte utilise un hash du texte normalisé. La proximité utilise SimHash 64 bits avec quatre bandes de 16 bits : seules les phrases partageant une bande deviennent candidates à une comparaison de Hamming. Cela évite une matrice quadratique globale tout en gardant un seuil testable.

## Statut épistémique

Un `claim_candidate` est une phrase extraite et traçable, pas une proposition démontrée. La similarité ne prouve ni équivalence sémantique, ni plagiat, ni antériorité, ni vérité. Toute promotion vers un claim corroboré exige une vérification d'entailment, de qualité des sources, de contradictions, de date, de droits et de domaine de validité.
