# Ω-AI-TRISTAN-LAB v0.2 — Ingestion + Reporting

## But

v0.2 transforme le MVP en outil utilisable localement : il peut lire des fichiers, enrichir une idée avec du contexte, produire un rapport OAK, puis persister les sorties.

## Composants

| Composant | Rôle |
|---|---|
| `DocumentIngestor` | Lit texte, Markdown, LaTeX, Python, JSON, YAML et PDF optionnel |
| `ChunkRecord` | Garde provenance, offsets et metadata |
| `ReportRenderer` | Génère JSON et Markdown |
| `Workspace` | Persiste `report.json`, `report.md`, `manifest.txt` |
| `LexicalSearchBackend` | Contrat de recherche local extensible |
| `NullVectorBackend` | Placeholder qui échoue explicitement si vector store absent |

## Pipeline

```text
idea + local files
→ ingest
→ chunk
→ lexical retrieval
→ enriched idea
→ AgentHarness
→ OAK/Bayes/IP/Revenue
→ report.json + report.md + manifest.txt
```

## Commande

```bash
python -m omega_ai_tristan_lab.cli \
  --idea "Construire un agent OAK-safe qui digère mes notes" \
  --ingest README.md omega_ai_manifesto.md \
  --context-query "OAK IP revenus prototype" \
  --output-dir omega_runs
```

## PDF

Le support PDF est volontairement optionnel :

```bash
python -m pip install -e ".[pdf]"
```

Sans `pypdf`, l'ingestion PDF retourne un avertissement au lieu de prétendre avoir lu le document.

## Règles OAK

- Ne jamais prétendre qu'un PDF scanné a été compris si aucun texte n'a été extrait.
- Toujours garder la provenance du chunk.
- Toujours persister les avertissements d'ingestion.
- Ne jamais confondre contexte récupéré et preuve.
- Garder `report.json` pour machine/API et `report.md` pour lecture humaine.

## v0.3 recommandé

- Ingestion ZIP multi-PDF.
- Extraction page/bbox via pipeline Rosette.
- Export hypergraphe `graph.json` / GraphML.
- Génération automatique d'issues GitHub depuis les résidus M⁻.
